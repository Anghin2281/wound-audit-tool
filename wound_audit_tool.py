
# Final Wound Audit Tool with Full Compliance Logic (No L39865)

import streamlit as st
import openai
from docx import Document
from PIL import Image
import fitz
from fpdf import FPDF
import tempfile
import base64
import datetime

client = openai.OpenAI()

st.set_page_config(page_title="CMS-Compliant Wound Audit Tool", layout="wide")
st.title("📋 CMS-Grade Wound Documentation Auditor")

st.markdown("""
This tool performs:
- CMS-compliant audits (L35125, L35041, A56696)
- Multi-note comparison (up to 4 uploads)
- Healing % calculation from wound volume
- Graft qualification analysis
- Graft layer recommendations
- Dressing validation
- Diagnosis-treatment-medication matching
- Infection identification
- PDF correction report generation

❌ L39865 (WPS) logic is excluded.
""")

uploaded_files = st.file_uploader("📁 Upload 1–4 Wound Care Notes (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], accept_multiple_files=True)
image_file = st.file_uploader("Optional: Upload Wound Image (.jpg, .png)", type=["jpg", "jpeg", "png"])

notes = []
if uploaded_files:
    for file in uploaded_files:
        content = ""
        if file.type == "application/pdf":
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                content += page.get_text()
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            docx_doc = Document(file)
            content = "\n".join([para.text for para in docx_doc.paragraphs])
        elif file.type == "text/plain":
            content = file.read().decode("utf-8")
        notes.append(content)

image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_context = "Wound image provided. Include granulation, exudate, and anatomical features in your analysis."

def build_prompt(note_set, image_data=""):
    combined_text = "\n---\n".join(note_set)
    return [
        {"role": "system", "content": (
            "You are a CMS wound documentation audit expert. Evaluate all notes chronologically using L35125, L35041, A56696. "
            "Check for conservative care, ICD/CPT validity, infection treatment, medication alignment, healing % (LxWxD), and graft eligibility. "
            "Suggest amniotic graft layer type (single, double, triple, quadruple) per wound characteristics. "
            "Identify dressing mismatches, diagnosis-treatment inconsistencies, and note copying. "
            "Generate a report with:\n"
            "1. What is correct\n"
            "2. What is missing\n"
            "3. Suggestions for compliance fixes\n"
            "4. Healing percentage & graft eligibility\n"
            "5. Recommended dressing & graft layer\n"
            "6. Final compliance score"
        )},
        {"role": "user", "content": image_data + "\n" + combined_text}
    ]

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for line in content.splitlines():
        pdf.multi_cell(0, 8, line)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        return tmpfile.name

if st.button("🚨 Run Audit & Generate PDF") and notes:
    with st.spinner("Running audit and compiling report..."):
        prompt = build_prompt(notes, image_context)
        response = client.chat.completions.create(model="gpt-4o", messages=prompt)
        audit_result = response.choices[0].message.content

        st.subheader("📋 Audit Report")
        st.markdown(audit_result)

        pdf_path = generate_pdf(audit_result)
        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            download_link = f'<a href="data:application/octet-stream;base64,{b64}" download="Wound_Audit_Report.pdf">📥 Download Audit Report PDF</a>'
            st.markdown(download_link, unsafe_allow_html=True)
else:
    st.info("Upload 1–4 wound care notes and click the button to begin.")
