import pandas as pd
from typing import Tuple, Dict, Any

# -------------------------------------------------------------------
# Attribution TP / TN / FP / FN pour un test
# -------------------------------------------------------------------
def classify_test(
    ischecker_status: str,
    llm_violation: bool | None,
) -> str:
    """
    Classe un test individuel en TP, TN, FP, FN ou UNDECIDED.

    Convention :
    - ischecker_status : "violation" ou "no_violation" (référence REGEX)
    - llm_violation    : True, False ou None (None = indécidable / parsing raté)

    Règles :
    - TP : isChecker = violation,  LLM = True
    - FN : isChecker = violation,  LLM = False
    - FP : isChecker = no_violation, LLM = True
    - TN : isChecker = no_violation, LLM = False
    - UNDECIDED : si llm_violation est None ou statut inconnu
    """
    if llm_violation is None:
        return "UNDECIDED"

    if ischecker_status == "violation":
        return "TP" if llm_violation else "FN"
    elif ischecker_status == "no_violation":
        return "FP" if llm_violation else "TN"
    else:
        # Statut inattendu côté isChecker
        return "UNDECIDED"


# -------------------------------------------------------------------
# Comparaison ligne à ligne dans un DataFrame
# -------------------------------------------------------------------
def add_comparison_columns(
    df: pd.DataFrame,
    confidence_threshold: float = 0.8,
) -> pd.DataFrame:
    """
    À partir d'un DataFrame contenant les colonnes :
    - ischecker_status  ("violation" / "no_violation")
    - violation         (bool ou None : résultat LLM parsé)
    - parsing_confidence (float)
    ajoute deux colonnes :
    - comparison_label : "TP","TN","FP","FN","UNDECIDED"
    - usable_for_metrics : True si parsing_confidence >= seuil et label != UNDECIDED

    :param df: DataFrame des tests (joint TSV + résultats LLM parsés)
    :param confidence_threshold: Seuil minimal de parsing_confidence pour
                                 inclure le test dans les métriques.
    :return: DataFrame avec colonnes supplémentaires
    """
    required_cols = {"ischecker_status", "violation", "parsing_confidence"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Colonnes manquantes pour la comparaison : {missing}"
        )

    # Application de classify_test ligne à ligne
    df = df.copy()
    df["comparison_label"] = df.apply(
        lambda row: classify_test(
            ischecker_status=row["ischecker_status"],
            llm_violation=row["violation"],
        ),
        axis=1,
    )

    # True si parsing_confidence suffisant ET label différent de UNDECIDED
    df["usable_for_metrics"] = df.apply(
        lambda row: (
            row["parsing_confidence"] is not None
            and row["parsing_confidence"] >= confidence_threshold
            and row["comparison_label"] != "UNDECIDED"
        ),
        axis=1,
    )

    return df

# -------------------------------------------------------------------
# Agrégation : matrice de confusion + métriques simples
# -------------------------------------------------------------------
def compute_confusion_and_metrics(
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Calcule la matrice de confusion et quelques métriques globales
    sur la base des tests marqués usable_for_metrics == True.

    Retourne un dictionnaire contenant :
    - counts: dict avec TP, TN, FP, FN
    - total: nombre total de tests utilisés
    - accuracy, precision, recall, f1 (calculés sur la classe "violation" comme positive)

    Si aucun test n'est utilisable, les métriques sont à None.
    """
    # On ne garde que les tests avec parsing_confidence suffisant et décision LLM
    df_used = df[df["usable_for_metrics"]]

    counts = {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    for label, n in df_used["comparison_label"].value_counts().items():
        if label in counts:
            counts[label] = int(n)

    TP = counts["TP"]
    TN = counts["TN"]
    FP = counts["FP"]
    FN = counts["FN"]

    total = TP + TN + FP + FN

    if total == 0:
        return {
            "counts": counts,
            "total": 0,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
        }

    # Métriques classiques sur la classe "violation" comme positive [web:580][web:582]
    accuracy = (TP + TN) / total if total > 0 else None
    precision = TP / (TP + FP) if (TP + FP) > 0 else None
    recall = TP / (TP + FN) if (TP + FN) > 0 else None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = None

    return {
        "counts": counts,
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
