
# Wound Audit Tool with CMS Compliance, TIMERS Framework, and Structured PDF Output (No Emoji)

import streamlit as st
import openai
from docx import Document
from PIL import Image
import fitz
from fpdf import FPDF
import tempfile
import base64

client = openai.OpenAI()

st.set_page_config(page_title="Wound Documentation Auditor", layout="wide")
st.title("CMS-Grade Wound Documentation Auditor")

st.markdown("""
This tool performs:
- CMS-compliant audits (L35125, L35041, A56696)
- TIMERS framework keyword detection and documentation analysis
- Healing percentage calculation based on wound volume
- Graft eligibility and layer recommendation
- Diagnosis-treatment-medication validation
- Infection treatment alignment
- Structured PDF output with sections:
  1. What is documented correctly
  2. What is missing
  3. Suggestions for corrections and rewording
""")

uploaded_files = st.file_uploader("Upload 1 to 4 Wound Notes (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], accept_multiple_files=True)
image_file = st.file_uploader("Optional: Upload Wound Image", type=["jpg", "jpeg", "png"])

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
    image_context = "Wound image provided. Include granulation, exudate, depth, and anatomical features."

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
        try:
            pdf.multi_cell(0, 8, line)
        except UnicodeEncodeError:
            pdf.multi_cell(0, 8, line.encode("latin-1", "replace").decode("latin-1"))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        return tmpfile.name

def build_prompt(note_set, image_data=""):
    combined_text = "\n---\n".join(note_set)
    return [
        {"role": "system", "content": (
            '''You are a CMS wound documentation auditor. Use L35125, L35041, and A56696. 
Apply the TIMERS framework:
- T: Debridement, necrosis, granulation, tissue types
- I: Infection or inflammation, antibiotic/antiseptic use
- M: Moisture balance, drainage type and dressing choice
- E: Edge of wound, epibole, migration, undermining
- R: Regeneration: granulation progress, graft application
- S: Social context: caregiver support, barriers to care

Audit for:
- Healing percentage based on wound volume (LxWxD)
- Eligibility for skin substitutes
- Appropriateness of dressing for wound type
- Infection diagnosis and whether treatment was documented and appropriate
- Consistency across multiple visits (healing trajectory)

Report should be divided into three sections:
1. What is documented correctly
2. What is missing
3. Suggestions for corrections or rewording
'''
        )},
        {"role": "user", "content": image_data + "\n" + combined_text}
    ]

if st.button("Run Audit and Generate PDF") and notes:
    with st.spinner("Auditing and generating PDF..."):
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
    st.info("Upload wound care notes and click to begin.")
