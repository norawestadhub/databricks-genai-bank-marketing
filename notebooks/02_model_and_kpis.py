# Databricks notebook source
# Databricks notebook source
# ===========================================
# 02 — Silver (rå+label), KPI og baseline-modell med full sporbarhet
# ===========================================
# Denne versjonen renamer "Unnamed: 0"/"Unnamed:_0" -> customer_id før vi gjør noe annet,
# så vi slipper SQL-problemer med spesialtegn. Vi unngår string-SQL for kolonneplukk.

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ---------- KONFIG ----------
CATALOG  = "workspace"                     # bruk "main" hvis UC-katalogen din heter 'main'
PROJECT  = "bank_marketing_demo"
SCHEMA   = f"{PROJECT}_db"
DATABASE = f"{CATALOG}.{SCHEMA}"

BRONZE          = f"{DATABASE}.bank_raw"        # rådata fra 01_ingest
SILVER          = f"{DATABASE}.bank_silver"     # rå + label + contact-fallback + customer_id
KPI_VIEW        = f"{DATABASE}.v_bank_kpi"      # nøkkeltall per segment
CUSTOMER_SCORES = f"{DATABASE}.customer_scores" # test-score + alle kolonner

spark.sql(f"USE {DATABASE}")
print("Bronze :", BRONZE)
print("Silver :", SILVER)
print("KPI    :", KPI_VIEW)
print("Scores :", CUSTOMER_SCORES)

# ===========================================
# 1) LES BRONZE (RÅDATA)
# ===========================================
df = spark.table(BRONZE)
print("Bronze rows:", df.count())
print("Bronze cols:", df.columns[:10], "... (tot:", len(df.columns), ")")

# ===========================================
# 2) NORMALISER ID + MINIMALE FELT
# ===========================================
# a) customer_id: gi rå-ID en stabilt navn
if "customer_id" not in df.columns:
    if "Unnamed: 0" in df.columns:
        df = df.withColumnRenamed("Unnamed: 0", "customer_id")
    elif "Unnamed:_0" in df.columns:
        df = df.withColumnRenamed("Unnamed:_0", "customer_id")

# Hvis ingen ID finnes i det hele tatt, generer en sekvensiell ID (stabil innen tabellen)
if "customer_id" not in df.columns:
    df = df.withColumn("customer_id", F.row_number().over(Window.orderBy(F.monotonically_increasing_id())))

# b) label (0/1) fra y hvis den finnes (minst mulig inngrep)
if "y" in df.columns:
    df = df.withColumn(
        "label",
        F.when(F.lower(F.col("y").cast("string")).isin("yes","ja","y","true","1"), F.lit(1)).otherwise(F.lit(0))
    )
else:
    df = df.withColumn("label", F.lit(None).cast("int"))

# c) contact-fallback: sørg for at kolonnen finnes for KPI/gruppevisning
if "contact" not in df.columns:
    df = df.withColumn("contact", F.lit("unknown"))

# d) cast typiske numeriske for enklere KPI/modell (selve verdiene endres ikke, kun typen)
for num in ["age","duration","campaign","pdays","previous","balance"]:
    if num in df.columns:
        df = df.withColumn(num, F.col(num).cast("double"))

# Skriv SILVER (rå + label + små hjelpere)
(df
 .write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema","true")
 .saveAsTable(SILVER)
)
print("✅ Skrev SILVER:", SILVER)

# ===========================================
# 3) KPI-VIEW (robust mot manglende felter)
# ===========================================
spark.sql(f"DROP VIEW IF EXISTS {KPI_VIEW}")
spark.sql(f"""
CREATE VIEW {KPI_VIEW} AS
SELECT
  CASE
    WHEN cast(age as double) IS NULL THEN 'unknown'
    WHEN cast(age as double) < 25 THEN '<25'
    WHEN cast(age as double) BETWEEN 25 AND 34 THEN '25-34'
    WHEN cast(age as double) BETWEEN 35 AND 44 THEN '35-44'
    WHEN cast(age as double) BETWEEN 45 AND 54 THEN '45-54'
    WHEN cast(age as double) BETWEEN 55 AND 64 THEN '55-64'
    ELSE '65+'
  END AS age_band,
  job,
  marital,
  contact,
  COUNT(*) AS total_customers,
  SUM(COALESCE(label,0)) AS term_deposit_yes_count,
  ROUND(SUM(COALESCE(label,0)) / NULLIF(COUNT(*),0), 4) AS term_deposit_yes_rate
FROM {SILVER}
GROUP BY
  CASE
    WHEN cast(age as double) IS NULL THEN 'unknown'
    WHEN cast(age as double) < 25 THEN '<25'
    WHEN cast(age as double) BETWEEN 25 AND 34 THEN '25-34'
    WHEN cast(age as double) BETWEEN 35 AND 44 THEN '35-44'
    WHEN cast(age as double) BETWEEN 45 AND 54 THEN '45-54'
    WHEN cast(age as double) BETWEEN 55 AND 64 THEN '55-64'
    ELSE '65+'
  END,
  job, marital, contact
""")
print("✅ KPI-view opprettet:", KPI_VIEW)
display(spark.sql(f"SELECT * FROM {KPI_VIEW} ORDER BY term_deposit_yes_rate DESC LIMIT 20"))

# ===========================================
# 4) BASELINE-MODELL (enkelt, forklarbart)
# ===========================================
# Vi beholder ALLE kolonner i score-tabellen for sporbarhet/“hvorfor”.
import pandas as pd

pdf = spark.table(SILVER).toPandas()

# Pass på at customer_id finnes i Pandas (hvis kolonnetegn ble endret underveis)
if "customer_id" not in pdf.columns:
    if "Unnamed: 0" in pdf.columns:
        pdf = pdf.rename(columns={"Unnamed: 0": "customer_id"})
    elif "Unnamed:_0" in pdf.columns:
        pdf = pdf.rename(columns={"Unnamed:_0": "customer_id"})

# Label til int
pdf["label"] = pdf["label"].fillna(0).astype(int)

# Plukk features: ta med typiske numeriske/kategoriske hvis de finnes
num_cols = [c for c in ["age","duration","campaign","pdays","previous","balance"] if c in pdf.columns]
cat_cols = [c for c in ["job","marital","education","default","housing","loan","contact","month","poutcome"] if c in pdf.columns]

# One-hot-encode kun for modellering (BERØRER IKKE originalkolonnene som vi lagrer)
pdf_enc = pd.get_dummies(pdf[num_cols + cat_cols], dummy_na=True)
X = pdf_enc.fillna(0)
y = pdf["label"]

# Installer sklearn hvis mangler
try:
    import sklearn  # noqa: F401
except ImportError:
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "scikit-learn"])

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

# Del i train/test (stratifiser hvis binær)
strata = y if y.nunique() == 2 else None
X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
    X, y, pdf.index, test_size=0.2, random_state=42, stratify=strata
)

# Tren enkel, forklarbar baseline (LR)
lr = LogisticRegression(max_iter=1000)
lr.fit(X_train, y_train)
y_prob = lr.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_prob)
print(f"✅ Baseline trent — AUC: {auc:.4f}")

# ===========================================
# 5) SCORE-TABELL MED ALLE KOLONNER
# ===========================================
# Vi tar ut originalradene for testindeksene, legger på 'score', og skriver ALT til Delta.
pdf_test = pdf.loc[idx_test].copy()
pdf_test["score"] = y_prob

# Sikre konsistent ID-kolonnenavn i testsettet
if "customer_id" not in pdf_test.columns:
    if "Unnamed: 0" in pdf_test.columns:
        pdf_test = pdf_test.rename(columns={"Unnamed: 0": "customer_id"})
    elif "Unnamed:_0" in pdf_test.columns:
        pdf_test = pdf_test.rename(columns={"Unnamed:_0": "customer_id"})

scores_sdf = spark.createDataFrame(pdf_test)
(scores_sdf
 .write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema","true")
 .saveAsTable(CUSTOMER_SCORES)
)
print("✅ Lagret score-tabell:", CUSTOMER_SCORES)

# Topp 20 kunder etter score – nå kan du se både score, label og alle attributter
display(spark.sql(f"""
SELECT customer_id, score, label, *
FROM {CUSTOMER_SCORES}
ORDER BY score DESC
LIMIT 20
"""))
