# Databricks GenAI Bank Marketing Demo

Dette prosjektet er utviklet som en **datadrevet analyse- og innsiktsplattform** for markedsføringsdata fra portugisisk banksektor, med fokus på hvordan Generativ AI (GenAI) kan brukes til å trekke ut handlingsrettede innsikter fra kampanjedata.  
Prosjektet er laget i Databricks og presenterer hele pipelinen fra datainnsamling til rapportering.

---

## 📊 Prosjektoversikt
1. **Datainnsamling**  
   - Henter rådata fra Kaggle (`marketing-of-the-portuguese-banking-institute`).
   - Lagrer som *Delta Tables* i Databricks for videre prosessering.

2. **Databehandling og modellering**  
   - Opprettelse av "Silver"-tabell med rensede og strukturerte data.
   - Utregning av KPI-er for responsrate per segment.
   - Trening av en enkel logistisk regresjonsmodell for å estimere sannsynligheten for at en kunde kjøper et termindepositum.

3. **Generativ AI-rapportering**  
   - Bruker OpenAI API for å generere ledervennlige sammendrag, forslag til tiltak og hypoteser for A/B-testing.
   - Q&A-modul for å svare på spesifikke forretningsspørsmål direkte fra data.
   - Rapporter lagres i `/reports/` som både **PDF** og **Markdown**.

---

## 🏆 Lederoppsummering (fra GenAI)

| Segment | Responsrate |
|---------|-------------|
| **65+ med ukjent yrke** | 75% |
| **65+ med administrativ stilling** | 33,3% |
| **25-34, ukjent yrke, single** | 23,3% |
| **45-54, arbeidsledig** | 0% |
| **35-44, arbeidsledig** | 0% |
| **55-64, pensjonert, single** | 2,7% |

---

## 🎯 Anbefalte tiltak
1. **Målrettet markedsføring** – Øk fokus på segmentene med høy responsrate, spesielt 65+.
2. **Tilpasset kommunikasjon** – Utvikle spesifikke kampanjer for lavresponssegmentene med vekt på deres behov.
3. **Kundelojalitetsprogram** – Implementer insentiver for å øke responsen i lavere segmenter.

---

## 🧪 Hypoteser for A/B-test
1. Tilpasset innhold for 65+ vil øke konverteringsraten ytterligere.
2. Bruk av visuelle elementer i kommunikasjonen vil øke responsen i lavresponssegmentene.
3. Tilbud om gratis rådgivning vil øke interessen blant arbeidsledige kunder.

---

## 📌 Q&A fra GenAI
**Prioriterte segmenter for neste kampanje:**

1. **65+ med ukjent yrke (divorced)**  
   - Kunder: 4  
   - Termindepositum: 3  
   - Andel: 75%  
   - Begrunnelse: Ekstremt høy konverteringsrate tross lavt antall kunder.

2. **55-64 med administrativ stilling (married)**  
   - Kunder: 434  
   - Termindepositum: 78  
   - Andel: 17,97%  
   - Begrunnelse: Stort kundegrunnlag med relativt høy konverteringsrate gir høy salgsvekstpotensial.

---

## 🛠 Teknologistack
- **Dataplattform:** Databricks (Delta Lake, Spark)
- **Datasett:** Kaggle – Marketing of the Portuguese Banking Institute
- **Maskinlæring:** scikit-learn (Logistisk regresjon)
- **Generativ AI:** OpenAI GPT-4o-mini
- **Lagring:** Delta Tables
- **Rapportering:** Pandas, Markdown, OpenAI Q&A

---

## 🚀 Hvordan kjøre prosjektet
1. Kjør `00_setup` for å opprette database og miljø.
2. Kjør `01_ingest_kaggle` for å hente rådata og lagre som Delta-tabell.
3. Kjør `02_model_and_kpi` for å generere KPI-view og trene baseline-modell.
4. Kjør `04_genai_report` for å generere lederrapport og Q&A.

---

## 📂 Mappestruktur
/00_setup
/01_ingest_kaggle
/02_model_and_kpi
/04_genai_report
/README.md
/reports/genai_report_.pdf
/reports/genai_report_.md

---

## 📈 Eksempelresultater
![Eksempelresultat](docs/example_kpi_chart.png)  
*Høyest responsrate finnes i segmentet 65+ med ukjent yrke.*
