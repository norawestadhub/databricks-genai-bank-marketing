# Databricks GenAI Bank Marketing Demo

Dette prosjektet er utviklet som en del av en søknad til **SpareBank 1** for stilling som *Senior Analytiker*.
Prosjektet demonstrerer bruk av Databricks, Delta Lake og Generativ AI (OpenAI) for analyse av markedsføringsdata
fra portugisisk banksektor.

## 📂 Prosjektstruktur

```
01_ingest_kaggle - Laster ned datasettet fra Kaggle og lagrer som Delta-tabell (bronze)
02_model_and_kpis - Bygger KPI-visning (gold) og en baseline prediksjonsmodell
03_genai_report - Bruker OpenAI API for å generere lederrapport og Q&A basert på KPI-data
data/ - Mappestruktur for evt. lokale filer (ikke versjonert)
```

## 📊 Datasett

Datasettet er hentet fra Kaggle:
[Marketing of the Portuguese Banking Institute](https://www.kaggle.com/datasets/mohammadeskandari7/marketing-of-the-portuguese-banking-institute)

**Beskrivelse:** 
Dataene beskriver telefonkampanjer for å selge bankinnskuddsprodukter, med informasjon om kunde, kampanjedetaljer og
om kunden aksepterte tilbudet (`y`-variabelen).

## 🔍 Analyseflyt

1. **Ingest** – Leser rådata fra Kaggle og lagrer dem i Databricks Delta-format
2. **KPI** – Lager aggregerte views for responsrater per segment (alder, yrke, kontaktmetode, etc.)
3. **Modellering** – Trener en enkel logistisk regresjonsmodell for å predikere sannsynlighet for aksept
4. **Generativ AI-rapport** – Bruker OpenAI til å lage ledervennlig oppsummering og forslag til tiltak

## 🛠️ Teknologier

- **Databricks** (notebooks, Delta Lake, MLflow)
- **PySpark** og **Pandas** for databehandling
- **scikit-learn** for maskinlæring
- **OpenAI API** for generativ analyse
- **KaggleHub** for datanedlasting

## 🚀 Hvordan kjøre prosjektet

1. Koble Databricks-workspace til GitHub og klon repoet som Databricks Repo
2. Sørg for at du har en aktiv cluster
3. Kjør notebookene i rekkefølgen:
- `01_ingest_kaggle`
- `02_model_and_kpis`
- `03_genai_report`
4. Sett `OPENAI_API_KEY` enten via Databricks Secrets, miljøvariabel eller widget

## 📈 Eksempelresultater

**KPI-tabell:**
| Age Band | Job | Marital | Response Rate |
|----------|----------|---------|---------------|
| 35-44 | admin. | single | 0.245 |
| 45-54 | blue-collar | married | 0.130 |

**GenAI lederrapport (eksempel):**
> Høyest respons i segmenter med alder 35-44 og yrke 'admin'. Lav respons i segment 'blue-collar' 45-54. 
> Tiltak: Mer personlig kontakt, teste alternative kampanjekanaler, øke kampanjefrekvens for toppsegmenter.

## 📄 Lisens

Dette prosjektet er kun ment som en teknisk demonstrasjon og har ingen kommersiell bruk.
