
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

st.set_page_config(page_title="CMS LCD-Based Wound Audit Tool", layout="wide")
st.markdown("<h1 style='color:#800000'>Strict CMS LCD Wound Audit Tool</h1>", unsafe_allow_html=True)

st.markdown("This tool audits wound documentation against CMS LCDs: L35125, L35041, A56696, and L37228.")

uploaded_files = st.file_uploader("Upload 1–10 Wound Notes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
image_file = st.file_uploader("Optional Wound Image", type=["jpg", "jpeg", "png"])

notes = []
note_info_headers = []
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

        header = []
        if patient: header.append(f"Patient: {patient.group(0).strip()}")
        if date: header.append(f"Date of Visit: {date.group(0).strip()}")
        if provider: header.append(f"Provider: {provider.group(0).strip()}")
        if facility: header.append(f"Facility: {facility.group(0).strip()}")
        note_info_headers.append("\n".join(header))

        notes.append(content + "\n" + raw)

image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Wound Image Uploaded", use_column_width=True)
    image_context = "Image uploaded. Consider granulation, exudate, periwound status."

def clean_text(text):
    return text.replace("•", "-").replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"').replace("’", "'")

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for line in clean_text(content).splitlines():
        safe = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, safe)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        return tmpfile.name

def build_prompt(notes, img="", compare=False, headers=None):
    combined = "\n---\n".join(notes)
    header_text = "\n\n".join(headers) if headers else ""
    instructions = '''
You are a strict CMS wound documentation auditor using only these sources:
- LCD L35125 (Novitas)
- LCD L35041 (CGS)
- A56696 (Billing/Coding)
- LCD L37228 (Wound Care)

Your job is to:
- Detect exact compliance or missing data
- Highlight what violates CMS documentation standards
- Flag failure to meet healing thresholds (<30–50% in 4 weeks)
- Identify incorrect or missing debridement type, justification, wound description, plan of care, pain, infection, graft use, and SMART goals

OUTPUT FORMAT:
=====
Patient: ...
Date of Visit: ...
Provider: ...
Facility: ...
CMS Compliance Rating: ...

Section 1: What is Documented Correctly
- Bullet points

Section 2: What is Missing or Non-Compliant
- Labeled by category (e.g., Debridement, Conservative Care, Infection)
- What is wrong
- Why it's non-compliant (with LCD reference if possible)

Section 3: Suggested Fixes and CMS Justified Corrections
1. Problem – Suggested Rewording
2. ...

Section 4: Final CMS Compliance Rating (Compliant / Partially Compliant / Non-Compliant)
=====
'''
    if compare:
        instructions += '\nCompare up to 10 notes over time. Track wound progression. Determine if graft usage is still justified or should stop based on CMS standards.'
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": header_text + "\n" + img + "\n" + combined}
    ]

if st.button("Run Audit", type="primary") and notes:
    compare_mode = len(notes) > 1
    with st.spinner("Running CMS audit..."):
        prompt = build_prompt(notes, image_context, compare_mode, note_info_headers)
        response = client.chat.completions.create(model="gpt-4o", messages=prompt)
        result = response.choices[0].message.content
        st.markdown(result)

        path = generate_pdf(result)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="CMS_LCD_Wound_Audit_Report.pdf">Download PDF Report</a>', unsafe_allow_html=True)
