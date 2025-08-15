# Databricks notebook source
# Databricks notebook source
# MAGIC %md
# MAGIC ## 00_setup – init DB and install project wheel (optional)

# COMMAND ----------
# Create widget for project name
dbutils.widgets.text("project", "bank_marketing_demo")

# Get widget value
project = dbutils.widgets.get("project")
database = f"{project}_db"

# Create and use database
spark.sql(f"CREATE DATABASE IF NOT EXISTS {database}")
spark.sql(f"USE {database}")
print("Using database:", database)

# COMMAND ----------
# MAGIC %md
# MAGIC ### (Optional) Install your packaged wheel if you use VS Code modules
# MAGIC Upload wheel to /FileStore/wheels/ and uncomment below

# COMMAND ----------
# %pip install /dbfs/FileStore/wheels/bankdemo-0.1.0-py3-none-any.whl
