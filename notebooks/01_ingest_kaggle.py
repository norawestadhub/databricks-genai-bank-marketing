# Databricks notebook source
# MAGIC %pip install --quiet kagglehub pandas
# MAGIC
# MAGIC import os, re, io, csv
# MAGIC import pandas as pd
# MAGIC import kagglehub
# MAGIC
# MAGIC # Prosjekt / DB (samme som 00_setup)
# MAGIC dbutils.widgets.text("project", "bank_marketing_demo")
# MAGIC project  = dbutils.widgets.get("project")
# MAGIC database = f"{project}_db"
# MAGIC table    = f"{database}.bank_raw"
# MAGIC spark.sql(f"CREATE DATABASE IF NOT EXISTS {database}")
# MAGIC spark.sql(f"USE {database}")
# MAGIC print("Using database:", database)
# MAGIC
# MAGIC # --- Last ned datasettet ---
# MAGIC local_dir = kagglehub.dataset_download(
# MAGIC     "mohammadeskandari7/marketing-of-the-portuguese-banking-institute"
# MAGIC )
# MAGIC print("Downloaded to:", local_dir)
# MAGIC
# MAGIC # Velg CSV (prøv foretrukne navn først, ellers største)
# MAGIC preferred = ["bank-additional-full.csv", "bank-additional.csv"]
# MAGIC csv_files = [f for f in os.listdir(local_dir) if f.lower().endswith(".csv")]
# MAGIC if not csv_files:
# MAGIC     raise FileNotFoundError(f"Ingen CSV-filer funnet i {local_dir}")
# MAGIC
# MAGIC chosen = next((f for f in preferred if f in csv_files), None)
# MAGIC if not chosen:
# MAGIC     csv_files = sorted(csv_files, key=lambda f: os.path.getsize(os.path.join(local_dir, f)), reverse=True)
# MAGIC     chosen = csv_files[0]
# MAGIC
# MAGIC csv_path = os.path.join(local_dir, chosen)
# MAGIC print("Valgt CSV:", csv_path)
# MAGIC
# MAGIC # --- Finn delimiter automatisk ---
# MAGIC with open(csv_path, "r", encoding="utf-8", errors="ignore") as fh:
# MAGIC     sample = fh.read(8192)
# MAGIC
# MAGIC try:
# MAGIC     sniff = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
# MAGIC     delim = sniff.delimiter
# MAGIC except Exception:
# MAGIC     # fallback: test ; og , og velg den som gir flest kolonner
# MAGIC     try_df_semicolon = pd.read_csv(io.StringIO(sample), sep=";", engine="python")
# MAGIC     try_df_comma     = pd.read_csv(io.StringIO(sample), sep=",",  engine="python")
# MAGIC     delim = ";" if try_df_semicolon.shape[1] >= try_df_comma.shape[1] else ","
# MAGIC
# MAGIC print("Oppdaget delimiter:", repr(delim))
# MAGIC
# MAGIC # --- Les hele fila med riktig delimiter (ingen transformasjoner) ---
# MAGIC pdf = pd.read_csv(csv_path, sep=delim, engine="python")
# MAGIC print("Pandas shape:", pdf.shape)
# MAGIC
# MAGIC # --- Minste nødvendige kolonnenavn-fiks for Delta ---
# MAGIC # (Delta tillater ikke tegn i settet ' ,;{}()\\n\\t=' og ikke tomme navn)
# MAGIC fixed_cols = []
# MAGIC for i, c in enumerate(pdf.columns):
# MAGIC     name = "" if c is None else str(c)
# MAGIC     if (name.strip() == ""):
# MAGIC         fixed_cols.append(f"col_{i}")
# MAGIC     else:
# MAGIC         fixed_cols.append(re.sub(r"[ ,;{}\(\)\n\t=]+", "_", name).strip("_"))
# MAGIC pdf.columns = fixed_cols
# MAGIC
# MAGIC # --- Til Spark og lagre som Delta ---
# MAGIC df = spark.createDataFrame(pdf)  # bevarer råverdier; Spark vil typetolke automatisk
# MAGIC (
# MAGIC     df.write
# MAGIC       .format("delta")
# MAGIC       .mode("overwrite")
# MAGIC       .option("overwriteSchema", "true")
# MAGIC       .saveAsTable(table)
# MAGIC )
# MAGIC print(f"✅ Lagret som Delta-tabell: {table}")
# MAGIC
# MAGIC # Rask sanity check
# MAGIC display(spark.sql(f"SELECT COUNT(*) AS n_rows FROM {table}"))
# MAGIC display(spark.table(table).limit(10))
# MAGIC