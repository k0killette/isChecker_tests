import os
from datetime import datetime
from typing import Optional

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_connection():
    """
    Crée une connexion PostgreSQL à partir des variables d'environnement.
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

def get_rule_id(conn, rule_name: str) -> Optional[int]:
    """
    Retourne rule_id à partir du rule_name dans dim_rules.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT rule_id
            FROM dim_rules
            WHERE rule_name = %s
            """,
            (rule_name,),
        )
        row = cur.fetchone()
        return row[0] if row else None

def get_or_create_test_id(
    conn,
    target_text: str,
    language: str,
    tag: Optional[str],
    ischecker_status: str,
    ischecker_message: Optional[str],
    profile: Optional[str] = None,
) -> int:
    """
    Retourne test_id pour un test donné, le crée si nécessaire.
    """
    with conn.cursor() as cur:
        # Recherche d'un test identique
        cur.execute(
            """
            SELECT test_id
            FROM dim_tests
            WHERE target_text = %s
              AND language = %s
              AND COALESCE(tag, '') = COALESCE(%s, '')
              AND ischecker_status = %s
            """,
            (target_text, language, tag, ischecker_status),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        # Insertion d'un nouveau test
        cur.execute(
            """
            INSERT INTO dim_tests (
                target_text, language, tag,
                ischecker_status, ischecker_message, profile
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING test_id
            """,
            (target_text, language, tag, ischecker_status, ischecker_message, profile),
        )
        new_id = cur.fetchone()[0]
        return new_id

def get_or_create_campaign_id(
    conn,
    llm_model_name: str,
    llm_provider: str,
    temperature: float,
    top_p: float,
    presence_penalty: float,
    description: Optional[str] = None,
) -> int:
    """
    Retourne campaign_id pour une combinaison (model, hyperparamètres), le crée si nécessaire.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT campaign_id
            FROM dim_campaigns
            WHERE llm_model_name = %s
              AND COALESCE(llm_provider, '') = COALESCE(%s, '')
              AND temperature = %s
              AND top_p = %s
              AND presence_penalty = %s
            """,
            (llm_model_name, llm_provider, temperature, top_p, presence_penalty),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute(
            """
            INSERT INTO dim_campaigns (
                llm_model_name, llm_provider,
                temperature, top_p, presence_penalty, description, start_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING campaign_id
            """,
            (llm_model_name, llm_provider, temperature, top_p, presence_penalty, description),
        )
        new_id = cur.fetchone()[0]
        return new_id

def insert_fact_results(
    conn,
    df_results: pd.DataFrame,
    campaign_id: int,
) -> None:
    """
    Insère les résultats LLM dans fact_results.

    df_results doit contenir au minimum :
    - rule_name
    - target_text
    - language
    - tag (optionnel)
    - ischecker_status
    - ischecker_message
    - llm_status
    - llm_error_message
    - parsing_confidence
    - source_file
    - match (bool)
    """
    required_cols = {
        "rule_name", "target_text", "language",
        "ischecker_status", "ischecker_message",
        "llm_status", "llm_error_message",
        "parsing_confidence", "source_file", "match",
    }
    missing = required_cols - set(df_results.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans df_results pour fact_results : {missing}")

    rows_to_insert = []

    with conn.cursor() as cur:
        for row in df_results.itertuples():
            # 1) rule_id
            rule_id = get_rule_id(conn, row.rule_name)
            if rule_id is None:
                print(f"Règle inconnue dans dim_rules : {row.rule_name}, ligne ignorée.")
                continue

            # 2) test_id
            test_id = get_or_create_test_id(
                conn=conn,
                target_text=row.target_text,
                language=row.language,
                tag=getattr(row, "tag", None),
                ischecker_status=row.ischecker_status,
                ischecker_message=row.ischecker_message,
                profile=getattr(row, "profile", None),
            )

            # 3) champ match : True si LLM et isChecker sont d'accord, False sinon
            match = bool(row.match)

            rows_to_insert.append(
                (
                    rule_id,
                    test_id,
                    campaign_id,
                    row.llm_status,
                    row.llm_error_message,
                    float(row.parsing_confidence) if row.parsing_confidence is not None else None,
                    match,
                    row.source_file,
                )
            )

        if not rows_to_insert:
            print("Aucune ligne à insérer dans fact_results.")
            return

        execute_values(
            cur,
            """
            INSERT INTO fact_results (
                rule_id, test_id, campaign_id,
                llm_status, llm_message, parsing_confidence,
                match, source_file
            )
            VALUES %s
            """,
            rows_to_insert,
        )

    conn.commit()
    print(f"{len(rows_to_insert)} lignes insérées dans fact_results.")
