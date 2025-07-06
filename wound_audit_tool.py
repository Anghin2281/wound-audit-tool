
# Final Wound Audit Tool with Structured PDF Output

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
This tool performs CMS-compliant documentation audits using:
- LCDs L35125 (Novitas), L35041, A56696
- TIMERS framework
- Healing trajectory and graft justification
- Dressing/medication/treatment alignment
- Infection identification and matching care

Outputs PDF with:
1. What is documented correctly
2. What is missing
3. Numbered suggestions for rewording or improvement
""")

uploaded_files = st.file_uploader("Upload 1 to 4 Wound Notes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
image_file = st.file_uploader("Optional: Upload Wound Image", type=["jpg", "jpeg", "png"])

notes = []
if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        content = f"Note {idx+1} - File Name: {file.name}\n"
        if file.type == "application/pdf":
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                content += page.get_text()
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            docx_doc = Document(file)
            content += "\n".join([para.text for para in docx_doc.paragraphs])
        elif file.type == "text/plain":
            content += file.read().decode("utf-8")

        # Extract identifiers
        patient = re.search(r"(HILDA GONZALES|Patient:.*|Name:.*)", content)
        date = re.search(r"Visited on:.*", content)
        provider = re.search(r"by:.*(NP|MD|DO|PA).*", content)
        facility = re.search(r"(South Texas Advanced Wound Care|Facility:.*|Clinic:.*)", content)

        header = f"\n===== Note {idx + 1} =====\n"
        if patient: header += f"{patient.group(0)}\n"
        if date: header += f"{date.group(0)}\n"
        if provider: header += f"Provider: {provider.group(0)}\n"
        if facility: header += f"Facility: {facility.group(0)}\n"

        notes.append(header + "\n" + content)

image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_context = "Wound image provided. Consider granulation, exudate, depth, margins."

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
            "You are a CMS wound documentation auditor. Use LCDs L35125, L35041, A56696. "
            "Apply the TIMERS framework. Evaluate healing trajectory, dressing choice, diagnosis-treatment match, "
            "infection signs and care alignment. Consider image data if available. "
            "For each note provided, return this exact structure:

"
            "===== AUDIT REPORT STRUCTURE START =====
"
            "Section 1: What is documented correctly (bullet points)
"
            "Section 2: What is missing or insufficient (bullet points)
"
            "Section 3: Numbered list of issues with suggested rewording or correction
"
            "===== AUDIT REPORT STRUCTURE END =====

"
            "Only use clean plain text. Do not include emojis or special symbols."
        )},
        {"role": "user", "content": image_data + "\n" + joined}
    ]

if st.button("Run Audit and Generate PDF") and notes:
    with st.spinner("Running structured CMS audit..."):
        prompt = build_prompt(notes, image_context)
        response = client.chat.completions.create(model="gpt-4o", messages=prompt)
        audit_result = response.choices[0].message.content

        st.subheader("Audit Report")
        st.markdown(audit_result)

        pdf_path = generate_pdf(audit_result)
        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            link = f'<a href="data:application/octet-stream;base64,{b64}" download="Wound_Audit_Structured_Report.pdf">Download PDF Report</a>'
            st.markdown(link, unsafe_allow_html=True)
else:
    st.info("Upload wound notes and click the audit button.")
