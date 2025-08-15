# Databricks notebook source
# --- Kjør rapport og Q&A, vis alltid tekstlig output ---
md = md_table(kpi_pdf, 30)

leader_report = None
qna_example = None
errors = []

# 1) Generer lederrapport
try:
    leader_report = gen_report(md)
except Exception as e:
    errors.append(f"Lederapport feilet: {e}")
    leader_report = (
        "⚠️ Klarte ikke å generere lederrapport (API-feil). "
        "Her er en enkel fallback-beskrivelse basert på KPI-tabellen:\n"
        "- Se etter segmenter med høyest 'term_deposit_yes_rate' og stort 'total_customers'.\n"
        "- Prioriter 2–3 av disse for neste kampanje.\n"
        "- Test alternative kontaktkanaler der rate er høy men volumet er lavt."
    )

# 2) Generer eksempel-Q&A
try:
    qna_example = ask(
        "Hvilke 2 segmenter bør vi prioritere i neste kampanje, og hvorfor?",
        md
    )
except Exception as e:
    errors.append(f"Q&A feilet: {e}")
    # Data-drevet fallback (enkel heuristikk)
    top = (
        kpi_pdf.sort_values("term_deposit_yes_rate", ascending=False)
               .head(2)[["age_band","job","marital","term_deposit_yes_rate","total_customers"]]
               .to_dict(orient="records")
    )
    bullets = "\n".join(
        [f"- {r['age_band']}, {r['job']}, {r['marital']} – rate {r['term_deposit_yes_rate']:.3f} (n={r['total_customers']})"
         for r in top]
    )
    qna_example = (
        "⚠️ Klarte ikke å generere Q&A med GenAI (API-feil). Foreslåtte prioriterte segmenter basert på KPI:\n"
        f"{bullets}\n"
        "Tiltak: målrett budskap mot disse segmentene, test kanal og tidspunkt."
    )

# 3) Vis rapportene tydelig
print("=== LEDERRAPPORT ===\n", leader_report)
print("\n=== EKSEMPEL Q&A ===\n", qna_example)

# 4) (Valgfritt) logg til MLflow, men ikke la feil her stoppe visning
try:
    import mlflow
    mlflow.set_experiment(f"/Shared/{PROJECT}")
    with mlflow.start_run(run_name="genai_summary_safe"):
        mlflow.log_text(leader_report, "leader_report.txt")
        mlflow.log_text(qna_example, "qna_example.txt")
        mlflow.log_metric("kpi_rows_used", int(min(30, len(kpi_pdf))))
except Exception as e:
    errors.append(f"MLflow-logging hoppet over: {e}")

# 5) Hvis noe feilet, skriv en kort status nederst (etter at rapporten er vist)
if errors:
    print("\n--- Tekniske merknader (påvirker ikke visningen over) ---")
    for msg in errors:
        print("•", msg)


# COMMAND ----------

# --- Lagre rapport-output som PDF + Markdown inne i repoet ---

%pip install --quiet reportlab

# COMMAND ----------
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# 1) Finn repo-roten (i en Databricks Repo peker '.' på repo-katalogen)
repo_root = os.getcwd()         # f.eks. /Workspace/Repos/<user>/<repo>
out_dir   = os.path.join(repo_root, "reports")
os.makedirs(out_dir, exist_ok=True)

ts = datetime.now().strftime("%Y-%m-%d_%H%M")
pdf_path = os.path.join(out_dir, f"genai_report_{ts}.pdf")
md_path  = os.path.join(out_dir, f"genai_report_{ts}.md")

# 2) Markdown-kopi (greit for Git-lesbarhet)
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# Lederoppsummering (GenAI)\n\n")
    f.write(leader_report + "\n\n")
    f.write("# Q&A\n\n")
    f.write(qna_example + "\n")

# 3) Lag en enkel, pen PDF med reportlab
def draw_wrapped_text(c, text, x, y, max_width):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if stringWidth(test, "Helvetica", 11) < max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= 14
            line = w
    if line:
        c.drawString(x, y, line)
        y -= 18
    return y

c = canvas.Canvas(pdf_path, pagesize=A4)
width, height = A4
margin = 2 * cm
x = margin
y = height - margin

c.setTitle("GenAI-lederrapport")

# Tittel
c.setFont("Helvetica-Bold", 14)
c.drawString(x, y, "GenAI-lederrapport")
y -= 20
c.setFont("Helvetica", 9)
c.drawString(x, y, f"Generert: {ts}")
y -= 24

# Lederoppsummering
c.setFont("Helvetica-Bold", 12)
c.drawString(x, y, "Lederoppsummering")
y -= 18
c.setFont("Helvetica", 11)
for block in leader_report.split("\n"):
    if y < margin + 40:
        c.showPage(); y = height - margin; c.setFont("Helvetica", 11)
    y = draw_wrapped_text(c, block, x, y, width - 2*margin)

# Q&A
c.setFont("Helvetica-Bold", 12)
if y < margin + 60:
    c.showPage(); y = height - margin
c.drawString(x, y, "Q&A")
y -= 18
c.setFont("Helvetica", 11)
for block in qna_example.split("\n"):
    if y < margin + 40:
        c.showPage(); y = height - margin; c.setFont("Helvetica", 11)
    y = draw_wrapped_text(c, block, x, y, width - 2*margin)

c.save()

print("✅ Lagret:")
print("PDF: ", pdf_path)
print("MD : ", md_path)
print("\nGå til Repos-panelet (venstre), åpne mappen 'reports', og commit/push til GitHub.")
