
# Final Wound Audit Tool: Full Structured Report with Note Info and Numbered Fixes

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

st.set_page_config(page_title="Wound Documentation Auditor", layout="wide")
st.title("CMS-Grade Wound Documentation Auditor")

st.markdown("""
Upload up to 4 wound care notes. This tool audits based on:
- LCDs L35125, L35041, A56696
- TIMERS framework
- CMS healing trajectory and graft justification
- Dressing and infection treatment alignment

The downloadable PDF report includes:
- Note identifiers (patient, date, provider, facility)
- Three structured audit sections:
  1. What is documented correctly
  2. What is missing
  3. Numbered corrections with suggestions
""")

uploaded_files = st.file_uploader("Upload 1 to 4 Wound Notes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
image_file = st.file_uploader("Optional: Upload Wound Image", type=["jpg", "jpeg", "png"])

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

        # Extract identifiers
        patient = re.search(r"(HILDA GONZALES|Patient[:\s]*[\w\s]+|Name[:\s]*[\w\s]+)", raw)
        date = re.search(r"Visited on[:\s]*[\w\s\-\d:]+", raw)
        provider = re.search(r"(by[:\s]*[\w\s,]+(?:NP|MD|DO|PA)[\w\s]*)", raw)
        facility = re.search(r"(South Texas Advanced Wound Care|Facility[:\s]*[\w\s]+|Clinic[:\s]*[\w\s]+)", raw)

        if patient: content += f"Patient Name: {patient.group(0).strip()}\n"
        if date: content += f"{date.group(0).strip()}\n"
        if provider: content += f"Provider: {provider.group(0).strip()}\n"
        if facility: content += f"Facility: {facility.group(0).strip()}\n"

        notes.append(content + "\n" + raw)

image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_context = "Wound image provided. Consider granulation, exudate, margins, and depth."

def clean_text(text):
    return (
        text.replace("•", "-").replace("–", "-").replace("—", "-")
            .replace("“", '"').replace("”", '"').replace("’", "'")
    )

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    safe_content = clean_text(content)
    for line in safe_content.splitlines():
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

def build_prompt(note_set, image_data=""):
    joined = "\n---\n".join(note_set)
    return [
        {"role": "system", "content": (
            '''You are a CMS wound documentation auditor. Use LCDs L35125, L35041, A56696.
Apply TIMERS (Tissue, Infection, Moisture, Edge, Regeneration, Social), assess wound healing trajectory, dressing appropriateness, infection-treatment match, and graft justification.

For each note uploaded, return this exact report format:

===== NOTE X =====
File Name: <uploaded_file>
Patient Name: <from note>
Date of Visit: <from note>
Provider: <from note>
Facility: <from note>

===== AUDIT REPORT STRUCTURE START =====
Section 1: What is Documented Correctly
- Item 1
- Item 2

Section 2: What is Missing or Insufficient
- Missing item 1
- Missing item 2

Section 3: Numbered Corrections and Suggested Fixes
1. Problem - Suggested fix
2. Problem - Suggested fix
===== AUDIT REPORT STRUCTURE END =====

Use only plain text. Do not include emojis or formatting codes.'''
        )},
        {"role": "user", "content": image_data + "\n" + joined}
    ]

if st.button("Run Audit and Generate PDF") and notes:
    with st.spinner("Running CMS audit..."):
        prompt = build_prompt(notes, image_context)
        response = client.chat.completions.create(model="gpt-4o", messages=prompt)
        audit_result = response.choices[0].message.content

        st.subheader("Audit Report")
        st.markdown(audit_result)

        pdf_path = generate_pdf(audit_result)
        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            download_link = f'<a href="data:application/octet-stream;base64,{b64}" download="Wound_Audit_Report.pdf">Download PDF Report</a>'
            st.markdown(download_link, unsafe_allow_html=True)
else:
    st.info("Upload documentation and click the button to audit.")
