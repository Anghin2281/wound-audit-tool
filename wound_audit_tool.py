
import streamlit as st
import openai
from docx import Document
from PIL import Image
import fitz
from fpdf import FPDF
import tempfile
import base64
import re

client = openai.OpenAI()

st.set_page_config(page_title="CMS Wound Audit Tool", layout="wide")
st.markdown("<h1 style='color:#800000'>CMS-Grade Wound Audit Tool</h1>", unsafe_allow_html=True)

st.markdown("""
Upload 1–10 wound documentation files.  
This tool performs:
- Single audits (if 1 file)
- Multi-note chronological comparison audits (if 2–10 files)
""")

uploaded_files = st.file_uploader("Upload Wound Notes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
image_file = st.file_uploader("Optional Wound Image", type=["jpg", "jpeg", "png"])

notes = []
if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        content = f"===== NOTE {idx+1} =====\nFile Name: {file.name}\n"
        raw = ""
        if file.type == "application/pdf":
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                raw += page.get_text()
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            docx_doc = Document(file)
            raw = "\n".join([para.text for para in docx_doc.paragraphs])
        elif file.type == "text/plain":
            raw = file.read().decode("utf-8")

        patient = re.search(r"(Patient[:\s]*[\w\s]+|Name[:\s]*[\w\s]+)", raw)
        date = re.search(r"Visited on[:\s]*[\w\s\-\d:]+", raw)
        provider = re.search(r"(by[:\s]*[\w\s,]+(?:NP|MD|DO|PA)[\w\s]*)", raw)
        facility = re.search(r"(Facility[:\s]*[\w\s]+|Clinic[:\s]*[\w\s]+)", raw)

        if patient: content += f"Patient Name: {patient.group(0).strip()}\n"
        if date: content += f"{date.group(0).strip()}\n"
        if provider: content += f"Provider: {provider.group(0).strip()}\n"
        if facility: content += f"Facility: {facility.group(0).strip()}\n"

        notes.append(content + "\n" + raw)

image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_context = "Wound image uploaded. Consider granulation, margins, exudate."

def clean_text(text):
    return (
        text.replace("•", "-").replace("–", "-").replace("—", "-")
            .replace("“", '"').replace("”", '"').replace("’", "'")
    )

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    safe = clean_text(content)
    for line in safe.splitlines():
        if line.strip() == "":
            pdf.ln()
        else:
            try:
                pdf.multi_cell(0, 8, line)
            except UnicodeEncodeError:
                pdf.multi_cell(0, 8, line.encode("latin-1", "replace").decode("latin-1"))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        return tmpfile.name

def build_prompt(notes, img="", compare=False):
    full = "\n---\n".join(notes)
    if compare:
        instruction = '''You are a CMS wound documentation auditor. Use LCDs L35125, L35041, A56696.
Compare all uploaded notes chronologically. Evaluate for:
- TIMERS documentation
- Healing trajectory across notes (area, depth, granulation)
- Graft justification over time
- Compliance with dressing, debridement, and conservative care
- Documentation consistency
Format each note as:

===== NOTE X =====
File Name: <uploaded_file>
Patient Name: <from note>
Date of Visit: <from note>
Provider: <from note>
Facility: <from note>

===== AUDIT REPORT STRUCTURE START =====
Section 1: What is Documented Correctly
- Bullet 1
Section 2: What is Missing or Insufficient
- Bullet 1
Section 3: Numbered Corrections and Suggested Fixes
1. Problem - Suggested Fix
===== AUDIT REPORT STRUCTURE END ====='''
    else:
        instruction = '''You are a CMS wound documentation auditor. Use LCDs L35125, L35041, A56696.
Evaluate the single note using:
- TIMERS
- CMS wound documentation
- Skin substitute criteria
- Infection-treatment alignment
- Graft readiness and healing percent

Format output as:

===== NOTE X =====
File Name: <uploaded_file>
Patient Name: <from note>
Date of Visit: <from note>
Provider: <from note>
Facility: <from note>

===== AUDIT REPORT STRUCTURE START =====
Section 1: What is Documented Correctly
- Bullet 1
Section 2: What is Missing or Insufficient
- Bullet 1
Section 3: Numbered Corrections and Suggested Fixes
1. Problem - Suggested Fix
===== AUDIT REPORT STRUCTURE END ====='''

    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": img + "\n" + full}
    ]

run = st.button("Run Audit", type="primary")

if run and notes:
    compare_mode = len(notes) > 1
    with st.spinner("Auditing documentation..."):
        prompt = build_prompt(notes, image_context, compare=compare_mode)
        response = client.chat.completions.create(model="gpt-4o", messages=prompt)
        result = response.choices[0].message.content
        st.subheader("Audit Results")
        st.markdown(result)

        pdf_path = generate_pdf(result)
        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            link = f'<a href="data:application/octet-stream;base64,{b64}" download="Wound_Audit_Report.pdf">Download PDF Report</a>'
            st.markdown(link, unsafe_allow_html=True)
else:
    st.info("Upload 1–10 documents and click 'Run Audit'.")
