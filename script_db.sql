-- Familles de règles
CREATE TABLE dim_rule_families (
    family_id         SERIAL PRIMARY KEY,
    family_name       VARCHAR(50)  NOT NULL UNIQUE,
    family_description TEXT,
    total_rules       INT,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Sévérités
CREATE TABLE dim_severities (
    severity_id       SERIAL PRIMARY KEY,
    severity_level    INT         NOT NULL UNIQUE,
    severity_name     VARCHAR(20) NOT NULL,
    created_at        TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Règles
CREATE TABLE dim_rules (
    rule_id           SERIAL PRIMARY KEY,
    rule_name         VARCHAR(100) NOT NULL,
    rule_type         VARCHAR(50),
    rule_prompt       TEXT,
    prompt_file       VARCHAR(255),
    prompt_key        VARCHAR(100),
    regex_pattern     TEXT,
    total_tests       INT,
    family_id         INT NOT NULL REFERENCES dim_rule_families(family_id),
    severity_id       INT NOT NULL REFERENCES dim_severities(severity_id),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP
);

CREATE INDEX idx_rules_name      ON dim_rules(rule_name);
CREATE INDEX idx_rules_family    ON dim_rules(family_id);
CREATE INDEX idx_rules_severity  ON dim_rules(severity_id);

-- Tests (référence isChecker)
CREATE TABLE dim_tests (
    test_id           SERIAL PRIMARY KEY,
    target_text       TEXT        NOT NULL,
    language          VARCHAR(10) NOT NULL,
    tag               VARCHAR(50),
    ischecker_status  VARCHAR(50) NOT NULL,   -- violation / no_violation
    ischecker_message TEXT,
    profile           VARCHAR(50),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_test_language   ON dim_tests(language);
CREATE INDEX idx_test_status     ON dim_tests(ischecker_status);

-- Campagnes
CREATE TABLE dim_campaigns (
    campaign_id       SERIAL PRIMARY KEY,
    campaign_name     VARCHAR(100) NOT NULL UNIQUE,
    llm_model_name    VARCHAR(100) NOT NULL,
    llm_provider      VARCHAR(50),
    temperature       NUMERIC(3,2),
    top_p             NUMERIC(3,2),
    presence_penalty  NUMERIC(3,2),
    description       TEXT,
    start_date        TIMESTAMP,
    end_date          TIMESTAMP
);

CREATE INDEX idx_campaign_model  ON dim_campaigns(llm_model_name);

-- Résultats
CREATE TABLE fact_results (
    result_id         BIGSERIAL PRIMARY KEY,
    rule_id           INT NOT NULL REFERENCES dim_rules(rule_id),
    test_id           INT NOT NULL REFERENCES dim_tests(test_id),
    campaign_id       INT NOT NULL REFERENCES dim_campaigns(campaign_id),

    llm_status        VARCHAR(50),
    llm_message       TEXT,
    parsing_confidence NUMERIC(3,2),
    match             BOOLEAN NOT NULL,
    execution_duration INTERVAL,
    execution_date    TIMESTAMP NOT NULL DEFAULT NOW(),

    source_file       VARCHAR(255),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index pour accélérer les jointures et filtres fréquents
CREATE INDEX idx_results_rule       ON fact_results(rule_id);
CREATE INDEX idx_results_test       ON fact_results(test_id);
CREATE INDEX idx_results_campaign   ON fact_results(campaign_id);
CREATE INDEX idx_results_match      ON fact_results(match);
CREATE INDEX idx_results_exec_date  ON fact_results(execution_date);
CREATE INDEX idx_results_rule_campaign ON fact_results(rule_id, campaign_id);
CREATE INDEX idx_results_campaign_match ON fact_results(campaign_id, match);

