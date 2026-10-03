-- ============================================================
-- TABLE ACCOUNTS
-- ============================================================
create or replace TABLE ACCOUNTS (
  ACCOUNT_ID VARCHAR(10) NOT NULL,
  CUSTOMER_ID VARCHAR(10) NOT NULL,
  ACCOUNT_TYPE VARCHAR(20) NOT NULL,
  OPENED_DATE DATE NOT NULL,
  STATUS VARCHAR(20) NOT NULL,
  primary key (ACCOUNT_ID)
);

-- ============================================================
-- TABLE ALERTS
-- ============================================================
create or replace TABLE ALERTS (
  ALERT_ID VARCHAR(10) NOT NULL,
  TRANSACTION_ID VARCHAR(12) NOT NULL,
  ALERT_TYPE VARCHAR(30) NOT NULL,
  SEVERITY VARCHAR(10) NOT NULL,
  CREATED_AT TIMESTAMP_NTZ(9) NOT NULL,
  STATUS VARCHAR(20) NOT NULL,
  primary key (ALERT_ID)
);

-- ============================================================
-- TABLE CREDIT_PROFILES
-- ============================================================
create or replace TABLE CREDIT_PROFILES (
  LOAN_ACCOUNT_ID VARCHAR(10) NOT NULL,
  CUSTOMER_ID VARCHAR(10) NOT NULL,
  OUTSTANDING_AMOUNT NUMBER(18,2) NOT NULL,
  DAYS_PAST_DUE NUMBER(38,0) NOT NULL,
  CREDIT_SCORE NUMBER(38,0) NOT NULL,
  NPA_FLAG BOOLEAN NOT NULL DEFAULT FALSE,
  AS_OF_DATE DATE NOT NULL,
  primary key (LOAN_ACCOUNT_ID)
);

-- ============================================================
-- TABLE CUSTOMERS
-- ============================================================
create or replace TABLE CUSTOMERS (
  CUSTOMER_ID VARCHAR(10) NOT NULL,
  FULL_NAME VARCHAR(100) NOT NULL,
  RISK_SEGMENT VARCHAR(20) NOT NULL,
  KYC_STATUS VARCHAR(20) NOT NULL,
  ONBOARDED_DATE DATE NOT NULL,
  COUNTRY VARCHAR(50) NOT NULL,
  primary key (CUSTOMER_ID)
);

-- ============================================================
-- TABLE LIQUIDITY_SNAPSHOTS
-- ============================================================
create or replace TABLE LIQUIDITY_SNAPSHOTS (
  SNAPSHOT_DATE DATE NOT NULL,
  HQLA_AMOUNT NUMBER(20,2) NOT NULL,
  NET_CASH_OUTFLOWS_30D NUMBER(20,2) NOT NULL,
  LCR_RATIO NUMBER(10,2) NOT NULL,
  STATUS VARCHAR(20) NOT NULL,
  primary key (SNAPSHOT_DATE)
);

-- ============================================================
-- TABLE POLICY_CLAUSES
-- ============================================================
create or replace TABLE POLICY_CLAUSES (
  DOC_ID VARCHAR(20) NOT NULL,
  DOC_TITLE VARCHAR(200) NOT NULL,
  CLAUSE_NO VARCHAR(10) NOT NULL,
  CLAUSE_TITLE VARCHAR(200) NOT NULL,
  CLAUSE_TEXT VARCHAR(4000) NOT NULL,
  CITATION VARCHAR(50) NOT NULL
);

-- ============================================================
-- TABLE TRANSACTIONS
-- ============================================================
create or replace TABLE TRANSACTIONS (
  TRANSACTION_ID VARCHAR(12) NOT NULL,
  ACCOUNT_ID VARCHAR(10) NOT NULL,
  TRANSACTION_DATE TIMESTAMP_NTZ(9) NOT NULL,
  AMOUNT NUMBER(18,2) NOT NULL,
  CURRENCY VARCHAR(3) NOT NULL,
  TRANSACTION_TYPE VARCHAR(20) NOT NULL,
  COUNTERPARTY_NAME VARCHAR(100),
  COUNTERPARTY_COUNTRY VARCHAR(50),
  CHANNEL VARCHAR(20) NOT NULL,
  IS_FLAGGED BOOLEAN NOT NULL DEFAULT FALSE,
  FLAG_REASON VARCHAR(50),
  primary key (TRANSACTION_ID)
);

-- ============================================================
-- DYNAMIC TABLE RING_EDGES
-- ============================================================
create or replace dynamic table RING_EDGES(
  ACCOUNT_A,
  ACCOUNT_B,
  SHARED_ATTRIBUTE,
  SHARED_VALUE,
  LINK_STRENGTH
) target_lag = '1 hour' refresh_mode = AUTO initialize = ON_CREATE warehouse = COMPUTE_WH
 as
  WITH HUB_FILTER AS (
      -- Keep only counterparties paid by <= 8 distinct accounts (exclude hubs)
      SELECT COUNTERPARTY_NAME
      FROM VIGIL.CORE.TRANSACTIONS
      WHERE COUNTERPARTY_NAME IS NOT NULL
      GROUP BY COUNTERPARTY_NAME
      HAVING COUNT(DISTINCT ACCOUNT_ID) <= 8
  )
  SELECT
      T1.ACCOUNT_ID                AS ACCOUNT_A,
      T2.ACCOUNT_ID                AS ACCOUNT_B,
      'COUNTERPARTY'               AS SHARED_ATTRIBUTE,
      T1.COUNTERPARTY_NAME         AS SHARED_VALUE,
      COUNT(*)                     AS LINK_STRENGTH
  FROM VIGIL.CORE.TRANSACTIONS T1
  JOIN VIGIL.CORE.TRANSACTIONS T2
      ON  T1.COUNTERPARTY_NAME = T2.COUNTERPARTY_NAME
      AND T1.ACCOUNT_ID < T2.ACCOUNT_ID                          -- canonical ordering, no self-pairs
      AND ABS(DATEDIFF('hour', T1.TRANSACTION_DATE, T2.TRANSACTION_DATE)) <= 72
  JOIN HUB_FILTER HF
      ON T1.COUNTERPARTY_NAME = HF.COUNTERPARTY_NAME
  GROUP BY T1.ACCOUNT_ID, T2.ACCOUNT_ID, T1.COUNTERPARTY_NAME;

-- ============================================================
-- DYNAMIC TABLE RINGS
-- ============================================================
create or replace dynamic table RINGS(
  RING_ID,
  MEMBER_ACCOUNTS,
  SHARED_LINK,
  TRANSACTION_IDS,
  DETECTED_AT
) target_lag = '1 hour' refresh_mode = AUTO initialize = ON_CREATE warehouse = COMPUTE_WH
 as
  WITH
  -- Bidirectional adjacency (ignore SHARED_VALUE for component detection)
  ADJ AS (
      SELECT DISTINCT ACCOUNT_A AS NODE, ACCOUNT_B AS NBR FROM VIGIL.CORE.RING_EDGES
      UNION ALL
      SELECT DISTINCT ACCOUNT_B, ACCOUNT_A FROM VIGIL.CORE.RING_EDGES
  ),
  NODES AS (SELECT DISTINCT NODE FROM ADJ),

  -- Min-label propagation: 5 fixed iterations (handles diameter <= 5)
  L0 AS (SELECT NODE, NODE AS LBL FROM NODES),
  L1 AS (
      SELECT L0.NODE, LEAST(L0.LBL, MIN(N.LBL)) AS LBL
      FROM L0
      JOIN ADJ A ON L0.NODE = A.NODE
      JOIN L0 N ON A.NBR = N.NODE
      GROUP BY L0.NODE, L0.LBL
  ),
  L2 AS (
      SELECT L1.NODE, LEAST(L1.LBL, MIN(N.LBL)) AS LBL
      FROM L1
      JOIN ADJ A ON L1.NODE = A.NODE
      JOIN L1 N ON A.NBR = N.NODE
      GROUP BY L1.NODE, L1.LBL
  ),
  L3 AS (
      SELECT L2.NODE, LEAST(L2.LBL, MIN(N.LBL)) AS LBL
      FROM L2
      JOIN ADJ A ON L2.NODE = A.NODE
      JOIN L2 N ON A.NBR = N.NODE
      GROUP BY L2.NODE, L2.LBL
  ),
  L4 AS (
      SELECT L3.NODE, LEAST(L3.LBL, MIN(N.LBL)) AS LBL
      FROM L3
      JOIN ADJ A ON L3.NODE = A.NODE
      JOIN L3 N ON A.NBR = N.NODE
      GROUP BY L3.NODE, L3.LBL
  ),
  L5 AS (
      SELECT L4.NODE, LEAST(L4.LBL, MIN(N.LBL)) AS LBL
      FROM L4
      JOIN ADJ A ON L4.NODE = A.NODE
      JOIN L4 N ON A.NBR = N.NODE
      GROUP BY L4.NODE, L4.LBL
  ),

  -- Components with >= 3 members
  COMPONENTS AS (
      SELECT LBL AS COMPONENT_ID,
             ARRAY_AGG(DISTINCT NODE) WITHIN GROUP (ORDER BY NODE) AS MEMBER_ACCOUNTS,
             COUNT(DISTINCT NODE) AS MEMBER_COUNT
      FROM L5
      GROUP BY LBL
      HAVING COUNT(DISTINCT NODE) >= 3
  ),

  -- Dominant shared counterparty per component (most edges)
  DOMINANT_LINK AS (
      SELECT LA.LBL AS COMPONENT_ID,
             RE.SHARED_VALUE,
             SUM(RE.LINK_STRENGTH) AS TOTAL_STRENGTH
      FROM VIGIL.CORE.RING_EDGES RE
      JOIN L5 LA ON RE.ACCOUNT_A = LA.NODE
      JOIN L5 LB ON RE.ACCOUNT_B = LB.NODE
      WHERE LA.LBL = LB.LBL
        AND LA.LBL IN (SELECT COMPONENT_ID FROM COMPONENTS)
      GROUP BY LA.LBL, RE.SHARED_VALUE
      QUALIFY ROW_NUMBER() OVER (PARTITION BY LA.LBL ORDER BY SUM(RE.LINK_STRENGTH) DESC) = 1
  ),

  -- Collect transaction IDs for member accounts with the shared counterparty
  RING_TXNS AS (
      SELECT C.COMPONENT_ID,
             C.MEMBER_ACCOUNTS,
             C.MEMBER_COUNT,
             DL.SHARED_VALUE AS SHARED_LINK,
             ARRAY_AGG(DISTINCT T.TRANSACTION_ID) WITHIN GROUP (ORDER BY T.TRANSACTION_ID) AS TRANSACTION_IDS
      FROM COMPONENTS C
      JOIN DOMINANT_LINK DL ON C.COMPONENT_ID = DL.COMPONENT_ID
      JOIN L5 ON L5.LBL = C.COMPONENT_ID
      JOIN VIGIL.CORE.TRANSACTIONS T
          ON T.ACCOUNT_ID = L5.NODE
         AND T.COUNTERPARTY_NAME = DL.SHARED_VALUE
      GROUP BY C.COMPONENT_ID, C.MEMBER_ACCOUNTS, C.MEMBER_COUNT, DL.SHARED_VALUE
  )

  SELECT
      'RING-' || LPAD(ROW_NUMBER() OVER (ORDER BY COMPONENT_ID)::VARCHAR, 3, '0') AS RING_ID,
      MEMBER_ACCOUNTS,
      SHARED_LINK,
      TRANSACTION_IDS,
      CURRENT_TIMESTAMP() AS DETECTED_AT
  FROM RING_TXNS;

-- ============================================================
-- CORTEX SEARCH SERVICE POLICY_SEARCH
-- ============================================================
create or replace cortex search service POLICY_SEARCH
  ON SEARCH_TEXT
  attributes DOC_ID,DOC_TITLE,CLAUSE_NO,CLAUSE_TITLE,CITATION
  warehouse='COMPUTE_WH'
  target_lag='1 day'
  refresh_mode=INCREMENTAL
  as (
    SELECT
      DOC_ID,
      DOC_TITLE,
      CLAUSE_NO,
      CLAUSE_TITLE,
      CITATION,
      CLAUSE_TITLE || ': ' || CLAUSE_TEXT AS SEARCH_TEXT
    FROM VIGIL.CORE.POLICY_CLAUSES
  );

-- ============================================================
-- SEMANTIC VIEW VIGIL_SV
-- ============================================================
create or replace semantic view VIGIL_SV
  tables (
    VIGIL.CORE.CUSTOMERS primary key (CUSTOMER_ID) with synonyms=('customer','client','account holder','KYC') comment='Customer master with KYC status and risk segmentation.',
    VIGIL.CORE.ACCOUNTS primary key (ACCOUNT_ID) with synonyms=('account','bank account') comment='Bank accounts linked to customers, including type and status.',
    VIGIL.CORE.TRANSACTIONS primary key (TRANSACTION_ID) with synonyms=('transaction','txn','payment','remittance','deposit','withdrawal','transfer','structuring','smurfing','velocity','layering') comment='All financial transactions with counterparty, channel, and AML flag details.',
    VIGIL.CORE.ALERTS primary key (ALERT_ID,TRANSACTION_ID) with synonyms=('alert','AML alert','fraud alert','SAR') comment='AML/fraud alerts generated from flagged transactions.',
    VIGIL.CORE.LIQUIDITY_SNAPSHOTS primary key (SNAPSHOT_DATE) with synonyms=('LCR','liquidity','HQLA','Basel III','liquidity coverage ratio') comment='Daily Basel III Liquidity Coverage Ratio snapshots.',
    VIGIL.CORE.CREDIT_PROFILES primary key (CUSTOMER_ID,LOAN_ACCOUNT_ID) with synonyms=('NPA','non-performing asset','loan','credit','provisioning','substandard','doubtful','DPD','days past due') comment='Loan-level credit profiles with NPA classification.',
    VIGIL.CORE.RING_EDGES unique (ACCOUNT_A,ACCOUNT_B,SHARED_VALUE) with synonyms=('ring edge','graph edge','hub','shared counterparty','co-transaction') comment='Graph edges linking account pairs that share a counterparty within 72 hours, hub-filtered.',
    VIGIL.CORE.RINGS with synonyms=('ring','fraud ring','coordinated activity','connected component') comment='Connected components of 3+ accounts detected as coordinated activity rings.'
  )
  relationships (
    ACCOUNTS_TO_CUSTOMERS as ACCOUNTS(CUSTOMER_ID) references CUSTOMERS(CUSTOMER_ID),
    TRANSACTIONS_TO_ACCOUNTS as TRANSACTIONS(ACCOUNT_ID) references ACCOUNTS(ACCOUNT_ID),
    ALERTS_TO_TRANSACTIONS as ALERTS(TRANSACTION_ID) references TRANSACTIONS(TRANSACTION_ID),
    CREDIT_PROFILES_TO_CUSTOMERS as CREDIT_PROFILES(CUSTOMER_ID) references CUSTOMERS(CUSTOMER_ID),
    RING_EDGES_A_TO_ACCOUNTS as RING_EDGES(ACCOUNT_A) references ACCOUNTS(ACCOUNT_ID),
    RING_EDGES_B_TO_ACCOUNTS as RING_EDGES(ACCOUNT_B) references ACCOUNTS(ACCOUNT_ID)
  )
  facts (
    TRANSACTIONS.AMOUNT as AMOUNT comment='Transaction amount in CURRENCY',
    LIQUIDITY_SNAPSHOTS.HQLA_AMOUNT as HQLA_AMOUNT,
    LIQUIDITY_SNAPSHOTS.NET_CASH_OUTFLOWS_30D as NET_CASH_OUTFLOWS_30D,
    LIQUIDITY_SNAPSHOTS.LCR_RATIO as LCR_RATIO comment='HQLA_AMOUNT / NET_CASH_OUTFLOWS_30D * 100. Must be >= 100 for compliance.',
    CREDIT_PROFILES.OUTSTANDING_AMOUNT as OUTSTANDING_AMOUNT comment='Current outstanding loan balance'
  )
  dimensions (
    CUSTOMERS.CUSTOMER_ID as CUSTOMER_ID comment='Unique customer ID (CUS-NNNN)',
    CUSTOMERS.FULL_NAME as FULL_NAME,
    CUSTOMERS.RISK_SEGMENT as RISK_SEGMENT comment='Risk tier: LOW, MEDIUM, HIGH',
    CUSTOMERS.KYC_STATUS as KYC_STATUS comment='KYC state: VERIFIED, PENDING, EXPIRED',
    CUSTOMERS.COUNTRY as COUNTRY,
    CUSTOMERS.ONBOARDED_DATE as ONBOARDED_DATE,
    ACCOUNTS.ACCOUNT_ID as ACCOUNT_ID comment='Unique account ID (ACC-NNNN)',
    ACCOUNTS.CUSTOMER_ID as CUSTOMER_ID comment='FK to CUSTOMERS',
    ACCOUNTS.ACCOUNT_TYPE as ACCOUNT_TYPE,
    ACCOUNTS.STATUS as STATUS comment='ACTIVE, DORMANT, FROZEN, CLOSED',
    ACCOUNTS.OPENED_DATE as OPENED_DATE,
    TRANSACTIONS.TRANSACTION_ID as TRANSACTION_ID comment='Unique transaction ID (TXN-NNNNNN)',
    TRANSACTIONS.ACCOUNT_ID as ACCOUNT_ID comment='FK to ACCOUNTS',
    TRANSACTIONS.CURRENCY as CURRENCY,
    TRANSACTIONS.TRANSACTION_TYPE as TRANSACTION_TYPE,
    TRANSACTIONS.COUNTERPARTY_NAME as COUNTERPARTY_NAME,
    TRANSACTIONS.COUNTERPARTY_COUNTRY as COUNTERPARTY_COUNTRY comment='Country of the counterparty; high-risk countries include Myanmar, North Korea, Iran, Panama',
    TRANSACTIONS.CHANNEL as CHANNEL,
    TRANSACTIONS.IS_FLAGGED as IS_FLAGGED comment='TRUE if AML pattern detected',
    TRANSACTIONS.FLAG_REASON as FLAG_REASON comment='STRUCTURING_SUSPECTED, HIGH_RISK_COUNTRY, VELOCITY, or NULL',
    TRANSACTIONS.TRANSACTION_DATE as TRANSACTION_DATE,
    ALERTS.ALERT_ID as ALERT_ID comment='Unique alert ID (ALT-NNNN)',
    ALERTS.TRANSACTION_ID as TRANSACTION_ID comment='FK to TRANSACTIONS',
    ALERTS.ALERT_TYPE as ALERT_TYPE,
    ALERTS.SEVERITY as SEVERITY comment='LOW, MEDIUM, HIGH, CRITICAL',
    ALERTS.STATUS as STATUS comment='OPEN, INVESTIGATING, ESCALATED, CLOSED_TRUE_POS, CLOSED_FALSE_POS',
    ALERTS.CREATED_AT as CREATED_AT,
    LIQUIDITY_SNAPSHOTS.STATUS as STATUS comment='COMPLIANT or BREACH',
    LIQUIDITY_SNAPSHOTS.SNAPSHOT_DATE as SNAPSHOT_DATE,
    CREDIT_PROFILES.LOAN_ACCOUNT_ID as LOAN_ACCOUNT_ID comment='Unique loan ID (LN-NNNN)',
    CREDIT_PROFILES.CUSTOMER_ID as CUSTOMER_ID,
    CREDIT_PROFILES.DAYS_PAST_DUE as DAYS_PAST_DUE comment='Days interest/principal is overdue. >90 = NPA.',
    CREDIT_PROFILES.CREDIT_SCORE as CREDIT_SCORE,
    CREDIT_PROFILES.NPA_FLAG as NPA_FLAG comment='TRUE if classified as non-performing asset',
    CREDIT_PROFILES.AS_OF_DATE as AS_OF_DATE,
    RING_EDGES.ACCOUNT_A as ACCOUNT_A comment='First account in the edge (canonical: A < B)',
    RING_EDGES.ACCOUNT_B as ACCOUNT_B comment='Second account in the edge',
    RING_EDGES.SHARED_ATTRIBUTE as SHARED_ATTRIBUTE,
    RING_EDGES.SHARED_VALUE as SHARED_VALUE comment='The counterparty name shared between the two accounts',
    RING_EDGES.LINK_STRENGTH as LINK_STRENGTH comment='Number of transaction pairs forming this edge',
    RINGS.RING_ID as RING_ID comment='Ring identifier (RING-NNN)',
    RINGS.MEMBER_ACCOUNTS as MEMBER_ACCOUNTS comment='Array of account IDs in the ring',
    RINGS.SHARED_LINK as SHARED_LINK comment='Dominant shared counterparty',
    RINGS.TRANSACTION_IDS as TRANSACTION_IDS comment='Array of transaction IDs involved',
    RINGS.DETECTED_AT as DETECTED_AT
  )
  comment='Risk, Fraud and Regulatory Intelligence semantic view for banking and NBFC compliance. Covers AML detection (structuring, smurfing, high-risk jurisdiction remittances, transaction velocity, coordinated ring activity), Basel III liquidity coverage ratio (LCR) monitoring, and credit risk (NPA classification and provisioning per RBI IRAC norms). Synonyms: structuring, smurfing, remittance, NPA, non-performing asset, LCR, liquidity, hub, ring, fraud ring, velocity, layering.'
  ai_verified_queries (
    "0;1" AS ( 
QUESTION 'What are all the flagged transactions for account ACC-0007 and their associated alerts?' 
VERIFIED_AT 1791019456
VERIFIED_BY 'Semantic Model Generator'
ONBOARDING_QUESTION false
SQL 'SELECT t.TRANSACTION_ID, t.ACCOUNT_ID, t.TRANSACTION_DATE, t.AMOUNT, t.TRANSACTION_TYPE, t.CHANNEL, t.IS_FLAGGED, t.FLAG_REASON, a.ALERT_ID, a.ALERT_TYPE, a.SEVERITY, a.STATUS AS ALERT_STATUS FROM transactions AS t LEFT JOIN alerts AS a ON t.TRANSACTION_ID = a.TRANSACTION_ID WHERE t.ACCOUNT_ID = ''ACC-0007'' AND t.IS_FLAGGED = TRUE ORDER BY t.TRANSACTION_DATE'),
    "1;1" AS ( 
QUESTION 'What are the flagged transactions for account ACC-0012 and their compliance status?' 
VERIFIED_AT 1791019456
VERIFIED_BY 'Semantic Model Generator'
ONBOARDING_QUESTION false
SQL 'SELECT t.TRANSACTION_ID, t.ACCOUNT_ID, t.AMOUNT, t.CURRENCY, t.TRANSACTION_TYPE, t.COUNTERPARTY_NAME, t.COUNTERPARTY_COUNTRY, t.FLAG_REASON, CASE WHEN t.AMOUNT >= 500000 THEN ''EDD REQUIRED per POL-AML-002 Clause 3'' ELSE ''BELOW THRESHOLD'' END AS EDD_REQUIREMENT, ''No EDD record table exists - compliance status cannot be confirmed'' AS EDD_NOTE FROM transactions AS t WHERE t.ACCOUNT_ID = ''ACC-0012'' AND t.IS_FLAGGED = TRUE'),
    "2;1" AS ( 
QUESTION 'What is the velocity pattern for large transactions on account ACC-0019?' 
VERIFIED_AT 1791019456
VERIFIED_BY 'Semantic Model Generator'
ONBOARDING_QUESTION false
SQL 'SELECT TRANSACTION_ID, ACCOUNT_ID, TRANSACTION_DATE, AMOUNT, TRANSACTION_TYPE, IS_FLAGGED, FLAG_REASON, SUM(CASE WHEN TRANSACTION_TYPE IN (''WITHDRAWAL'', ''TRANSFER'') THEN AMOUNT ELSE 0 END) OVER () AS TOTAL_OUTFLOW, MAX(CASE WHEN TRANSACTION_TYPE = ''DEPOSIT'' THEN AMOUNT END) OVER () AS DEPOSIT_AMOUNT, ROUND(SUM(CASE WHEN TRANSACTION_TYPE IN (''WITHDRAWAL'', ''TRANSFER'') THEN AMOUNT ELSE 0 END) OVER () / NULLIF(MAX(CASE WHEN TRANSACTION_TYPE = ''DEPOSIT'' THEN AMOUNT END) OVER (), 0) * 100, 1) AS PCT_MOVED_OUT FROM transactions WHERE ACCOUNT_ID = ''ACC-0019'' AND AMOUNT >= 100000 ORDER BY TRANSACTION_DATE'),
    "3;1" AS ( 
QUESTION 'What fraud rings is account ACC-0031 connected to?' 
VERIFIED_AT 1791019456
VERIFIED_BY 'Semantic Model Generator'
ONBOARDING_QUESTION false
SQL 'SELECT r.RING_ID, r.SHARED_LINK, r.MEMBER_ACCOUNTS, ARRAY_SIZE(r.MEMBER_ACCOUNTS) AS MEMBER_COUNT, r.TRANSACTION_IDS, r.DETECTED_AT FROM rings AS r, TABLE(FLATTEN(r.MEMBER_ACCOUNTS)) AS f WHERE CAST(f.VALUE AS VARCHAR) = ''ACC-0031'''),
    "4;1" AS ( 
QUESTION 'What is our current liquidity coverage ratio compliance status?' 
VERIFIED_AT 1791019456
VERIFIED_BY 'Semantic Model Generator'
ONBOARDING_QUESTION false
SQL 'SELECT SNAPSHOT_DATE, HQLA_AMOUNT, NET_CASH_OUTFLOWS_30D, LCR_RATIO, STATUS FROM liquidity_snapshots ORDER BY SNAPSHOT_DATE DESC'),
    "5;1" AS ( 
QUESTION 'Which loan accounts are non-performing assets and what provisioning is required for each account?' 
VERIFIED_AT 1791019456
VERIFIED_BY 'Semantic Model Generator'
ONBOARDING_QUESTION false
SQL 'SELECT LOAN_ACCOUNT_ID, CUSTOMER_ID, OUTSTANDING_AMOUNT, DAYS_PAST_DUE, CREDIT_SCORE, NPA_FLAG, CASE WHEN DAYS_PAST_DUE > 90 AND DAYS_PAST_DUE <= 455 THEN ''Substandard'' WHEN DAYS_PAST_DUE > 455 THEN ''Doubtful'' ELSE ''Standard'' END AS SUB_CLASSIFICATION, CASE WHEN DAYS_PAST_DUE > 90 AND DAYS_PAST_DUE <= 455 THEN OUTSTANDING_AMOUNT * 0.15 WHEN DAYS_PAST_DUE > 455 THEN OUTSTANDING_AMOUNT * 0.25 ELSE 0 END AS PROVISION_REQUIRED FROM credit_profiles WHERE NPA_FLAG = TRUE ORDER BY DAYS_PAST_DUE DESC')
  )
  with extension (CA='{"tables":[{"name":"CUSTOMERS","dimensions":[{"name":"CUSTOMER_ID"},{"name":"FULL_NAME"},{"name":"RISK_SEGMENT"},{"name":"KYC_STATUS"},{"name":"COUNTRY"}],"time_dimensions":[{"name":"ONBOARDED_DATE"}]},{"name":"ACCOUNTS","dimensions":[{"name":"ACCOUNT_ID"},{"name":"CUSTOMER_ID"},{"name":"ACCOUNT_TYPE"},{"name":"STATUS"}],"time_dimensions":[{"name":"OPENED_DATE"}]},{"name":"TRANSACTIONS","dimensions":[{"name":"TRANSACTION_ID"},{"name":"ACCOUNT_ID"},{"name":"CURRENCY"},{"name":"TRANSACTION_TYPE"},{"name":"COUNTERPARTY_NAME"},{"name":"COUNTERPARTY_COUNTRY"},{"name":"CHANNEL"},{"name":"IS_FLAGGED"},{"name":"FLAG_REASON"}],"facts":[{"name":"AMOUNT"}],"time_dimensions":[{"name":"TRANSACTION_DATE"}],"measures":[{"name":"flagged_transaction_count","expr":"CASE WHEN IS_FLAGGED THEN 1 ELSE 0 END","data_type":"NUMBER","default_aggregation":"sum","description":"Count of transactions flagged for AML patterns","synonyms":["flagged count","suspicious transaction count"]},{"name":"flagged_transaction_amount","expr":"CASE WHEN IS_FLAGGED THEN AMOUNT ELSE 0 END","data_type":"NUMBER","default_aggregation":"sum","description":"Total amount of flagged transactions","synonyms":["flagged amount","suspicious amount"]},{"name":"deposit_total","expr":"CASE WHEN TRANSACTION_TYPE = ''DEPOSIT'' THEN AMOUNT ELSE 0 END","data_type":"NUMBER","default_aggregation":"sum","description":"Total deposit amount"}]},{"name":"ALERTS","dimensions":[{"name":"ALERT_ID"},{"name":"TRANSACTION_ID"},{"name":"ALERT_TYPE"},{"name":"SEVERITY"},{"name":"STATUS"}],"time_dimensions":[{"name":"CREATED_AT"}]},{"name":"LIQUIDITY_SNAPSHOTS","dimensions":[{"name":"STATUS"}],"facts":[{"name":"HQLA_AMOUNT"},{"name":"NET_CASH_OUTFLOWS_30D"},{"name":"LCR_RATIO"}],"time_dimensions":[{"name":"SNAPSHOT_DATE"}],"measures":[{"name":"breach_days","expr":"CASE WHEN STATUS = ''BREACH'' THEN 1 ELSE 0 END","data_type":"NUMBER","default_aggregation":"sum","description":"Count of days where LCR was below 100% (breach)","synonyms":["LCR breach count","non-compliant days"]}]},{"name":"CREDIT_PROFILES","dimensions":[{"name":"LOAN_ACCOUNT_ID"},{"name":"CUSTOMER_ID"},{"name":"DAYS_PAST_DUE"},{"name":"CREDIT_SCORE"},{"name":"NPA_FLAG"}],"facts":[{"name":"OUTSTANDING_AMOUNT"}],"time_dimensions":[{"name":"AS_OF_DATE"}],"measures":[{"name":"npa_loan_count","expr":"CASE WHEN NPA_FLAG THEN 1 ELSE 0 END","data_type":"NUMBER","default_aggregation":"sum","description":"Count of non-performing loan accounts"},{"name":"outstanding_npa_amount","expr":"CASE WHEN NPA_FLAG THEN OUTSTANDING_AMOUNT ELSE 0 END","data_type":"NUMBER","default_aggregation":"sum","description":"Total outstanding amount on NPA loans"},{"name":"npa_provisioning_required","expr":"CASE WHEN NPA_FLAG AND DAYS_PAST_DUE <= 455 THEN OUTSTANDING_AMOUNT * 0.15 WHEN NPA_FLAG AND DAYS_PAST_DUE > 455 THEN OUTSTANDING_AMOUNT * 0.25 ELSE 0 END","data_type":"NUMBER","default_aggregation":"sum","description":"Provisioning required per POL-CR-001: Substandard (up to 12 months NPA) at 15%, Doubtful at 25%","synonyms":["provision amount","NPA provision"]}]},{"name":"RING_EDGES","dimensions":[{"name":"ACCOUNT_A"},{"name":"ACCOUNT_B"},{"name":"SHARED_ATTRIBUTE"},{"name":"SHARED_VALUE"},{"name":"LINK_STRENGTH"}],"measures":[{"name":"distinct_accounts_per_counterparty","expr":"ACCOUNT_A","data_type":"VARCHAR","default_aggregation":"count_distinct","description":"Number of distinct accounts linked to a shared counterparty"}]},{"name":"RINGS","dimensions":[{"name":"RING_ID"},{"name":"MEMBER_ACCOUNTS"},{"name":"SHARED_LINK"},{"name":"TRANSACTION_IDS"}],"time_dimensions":[{"name":"DETECTED_AT"}]}],"relationships":[{"name":"ACCOUNTS_TO_CUSTOMERS","relationship_type":"many_to_one","join_type":"inner"},{"name":"TRANSACTIONS_TO_ACCOUNTS","relationship_type":"many_to_one","join_type":"inner"},{"name":"ALERTS_TO_TRANSACTIONS","relationship_type":"many_to_one","join_type":"inner"},{"name":"CREDIT_PROFILES_TO_CUSTOMERS","relationship_type":"many_to_one","join_type":"inner"},{"name":"RING_EDGES_A_TO_ACCOUNTS","relationship_type":"many_to_one","join_type":"inner"},{"name":"RING_EDGES_B_TO_ACCOUNTS","relationship_type":"many_to_one","join_type":"inner"}]}');

-- ============================================================
-- FUNCTION RING_LOOKUP
-- ============================================================
CREATE OR REPLACE FUNCTION "RING_LOOKUP"("P_ACCOUNT_ID" VARCHAR)
RETURNS OBJECT
LANGUAGE SQL
AS '
  SELECT OBJECT_CONSTRUCT(
    ''edges'', COALESCE(
      (SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
        ''account_a'', ACCOUNT_A, ''account_b'', ACCOUNT_B,
        ''shared_value'', SHARED_VALUE, ''link_strength'', LINK_STRENGTH
      )) FROM VIGIL.CORE.RING_EDGES 
      WHERE ACCOUNT_A = P_ACCOUNT_ID OR ACCOUNT_B = P_ACCOUNT_ID),
      PARSE_JSON(''[]'')),
    ''ring'', COALESCE(
      (SELECT OBJECT_CONSTRUCT(
        ''ring_id'', r.RING_ID, ''shared_link'', r.SHARED_LINK,
        ''member_accounts'', r.MEMBER_ACCOUNTS, ''transaction_ids'', r.TRANSACTION_IDS,
        ''member_count'', ARRAY_SIZE(r.MEMBER_ACCOUNTS)
      ) FROM VIGIL.CORE.RINGS r, TABLE(FLATTEN(r.MEMBER_ACCOUNTS)) f 
      WHERE f.VALUE::VARCHAR = P_ACCOUNT_ID LIMIT 1),
      PARSE_JSON(''{"status": "NO_RING_FOUND"}''))
  )
';

-- ============================================================
-- AGENT VIGIL_AGENT (spec from DESCRIBE AGENT)
-- ============================================================
CREATE OR REPLACE AGENT VIGIL.CORE.VIGIL_AGENT
FROM SPECIFICATION $$
{"orchestration":{"tool_not_accessible":"accept"},"instructions":{"response":"You are Vigil, a compliance copilot for banking and NBFC analysts. All data is synthetic. Every claim in your answer must cite a specific record ID (TRANSACTION_ID, ACCOUNT_ID, ALERT_ID, RING_ID, LOAN_ACCOUNT_ID or SNAPSHOT_DATE) AND a specific policy document plus clause (for example POL-AML-001 Clause 3), taken from the policy search results; never state a fact without a citation. Every policy citation must be written as the document ID followed by the clause, exactly as in the CITATION column returned by the policy search tool, e.g. POL-AML-003 Clause 2 or POL-CR-001 Clause 4. Quote the clause text after the citation. Never cite a clause number without its document ID. If you cannot find a confident policy clause, say so explicitly and state your uncertainty plainly instead of guessing. If the user does not specify which transaction, account or loan they mean and none is available from context, ask which one before answering; do not assume the most recent alert. For every fraud or AML question, also call the ring lookup tool for the account involved before answering, in addition to transaction data. There is no EDD record table, so say EDD status is unknown rather than inventing it. Never post, send or notify anything externally; you have no external tool, and if the user asks you to post or notify, say that no external connector is configured and that a human must do it. You are a copilot: a human signs off on every STR or filing, and you never file anything. Never state accuracy or efficiency percentages. Format every answer as: Verdict; Evidence (record IDs, amounts, dates); Policy citations (document plus clause with the clause text quoted); Confidence note.\n","orchestration":"For AML, fraud, or transaction questions: first call the analyst tool for transaction data, then call ring_lookup for the involved account, then call policy_search for the applicable regulation. For liquidity or credit questions: call the analyst tool then policy_search. Always use all three tools for AML questions before responding.\n"},"tools":[{"tool_spec":{"type":"cortex_analyst_text_to_sql","name":"analyst","description":"Query structured financial data: transactions, alerts, accounts, customers, credit profiles, liquidity snapshots, and detected fraud rings in VIGIL.CORE"}},{"tool_spec":{"type":"cortex_search","name":"policy_search","description":"Search regulatory and internal policy documents for applicable clauses and citations. Returns CITATION (e.g. POL-AML-003 Clause 2), DOC_ID, CLAUSE_NO, CLAUSE_TITLE, DOC_TITLE, and the clause text."}},{"tool_spec":{"type":"generic","name":"ring_lookup","description":"Look up fraud ring connections for a given account ID. Returns EDGE rows with neighboring accounts and shared counterparties, plus a RING row with RING_ID, member accounts, and transaction IDs. Returns NO_RING_FOUND if the account has no ring. Always call this for AML or fraud questions.","input_schema":{"type":"object","properties":{"p_account_id":{"type":"string","description":"The account ID to look up ring connections for, e.g. ACC-0031"}},"required":["p_account_id"]}}}],"tool_resources":{"analyst":{"semantic_view":"VIGIL.CORE.VIGIL_SV","execution_environment":{"type":"warehouse","warehouse":"COMPUTE_WH"}},"policy_search":{"search_service":"VIGIL.CORE.POLICY_SEARCH","max_results":5,"columns_and_descriptions":{"SEARCH_TEXT":{"description":"The clause title and full clause text","type":"string","searchable":true,"filterable":false},"CITATION":{"description":"The citation reference in format DOC_ID Clause NUMBER, e.g. POL-AML-003 Clause 2. Always use this exact string when citing a policy clause.","type":"string","searchable":false,"filterable":false},"DOC_ID":{"description":"The policy document identifier, e.g. POL-AML-001, POL-CR-001, POL-LIQ-001","type":"string","searchable":false,"filterable":true},"DOC_TITLE":{"description":"The policy document title","type":"string","searchable":false,"filterable":false},"CLAUSE_NO":{"description":"The clause number within the document","type":"string","searchable":false,"filterable":false},"CLAUSE_TITLE":{"description":"The clause heading","type":"string","searchable":false,"filterable":false}}},"ring_lookup":{"type":"function","identifier":"VIGIL.CORE.RING_LOOKUP","execution_environment":{"type":"warehouse","warehouse":"COMPUTE_WH"}}}}
$$;

-- ============================================================
-- STREAMLIT VIGIL_APP
-- ============================================================
create or replace streamlit VIGIL_APP
  from '@VIGIL.CORE.VIGIL_APP_STAGE'
  main_file='streamlit_app.py'
  query_warehouse='COMPUTE_WH'
  title='Vigil';

-- ============================================================
-- PROCEDURE _STAGE_FILE (helper used to upload app files)
-- ============================================================
CREATE OR REPLACE PROCEDURE "_STAGE_FILE"("STAGE_PATH" VARCHAR, "FILE_NAME" VARCHAR, "CONTENT" VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run'
EXECUTE AS CALLER
AS '
def run(session, stage_path, file_name, content):
    import tempfile, os
    td = tempfile.mkdtemp()
    fp = os.path.join(td, file_name)
    with open(fp, ''w'', encoding=''utf-8'') as f:
        f.write(content)
    session.file.put(fp, stage_path, auto_compress=False, overwrite=True)
    os.unlink(fp)
    os.rmdir(td)
    return f''{file_name} uploaded to {stage_path}''
';

-- ============================================================
-- FILE FORMAT RAW_FMT (used for stage readbacks)
-- ============================================================
CREATE OR REPLACE FILE FORMAT RAW_FMT
  RECORD_DELIMITER = 'NONE'
  FIELD_DELIMITER = 'NONE'
;

-- ============================================================
-- STAGE VIGIL_APP_STAGE: GET_DDL does not support stages ("Invalid object type: 'STAGE'"); no DDL printed
-- ============================================================