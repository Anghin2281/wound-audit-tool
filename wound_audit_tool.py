
# Final Wound Audit Tool with CMS Compliance, TIMERS, Identifiers, and Numbered Corrections (No Emojis)

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
This tool audits documentation against:
- LCDs: L35125 (Novitas), L35041, and A56696
- TIMERS framework: Tissue, Infection, Moisture, Edge, Regeneration, Social
- Healing trajectory: volume reduction, granulation, consistency across visits
- Dressing, graft use, infection management, diagnosis-treatment alignment

It outputs a structured report:
1. What is documented correctly
2. What is missing or incorrect
3. Numbered list of suggestions for correction or rewording

Also includes:
- Patient name
- Date of visit
- Provider name
- Facility name
""")

uploaded_files = st.file_uploader("Upload 1 to 4 Wound Notes (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], accept_multiple_files=True)
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

        # Extract patient identifiers
        patient_match = re.search(r"(?:Patient|Name|HILDA|MRN).*", content, re.IGNORECASE)
        date_match = re.search(r"(Visited on|Date).*?:?\s*(\d{4}[-\s]?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s?\d{0,2})", content)
        provider_match = re.search(r"(Edited by|Provider|Signed by).*", content, re.IGNORECASE)
        facility_match = re.search(r"(South Texas Advanced Wound Care|Facility:.*|Clinic:.*)", content)

        header = "\nPatient Summary for Note " + str(idx + 1) + ":\n"
        if patient_match:
            header += patient_match.group(0) + "\n"
        if date_match:
            header += "Date of Visit: " + date_match.group(0) + "\n"
        if provider_match:
            header += provider_match.group(0) + "\n"
        if facility_match:
            header += "Facility: " + facility_match.group(0) + "\n"

        notes.append(header + "\n" + content)

image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_context = "Wound image provided. Consider granulation, depth, exudate, and margin details."

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
- T: Document tissue type, granulation, necrosis, debridement
- I: Note signs of infection, antibiotic/antiseptic use, biofilm management
- M: Match drainage type and amount to appropriate dressing
- E: Evaluate wound edge status and progression
- R: Track granulation growth, healing percent, graft application
- S: Include social context, caregiver, and adherence factors

For each note:
- Extract and report patient name, date of visit, provider, and facility (if detectable)
- Calculate healing trajectory from volume if multiple notes
- Determine graft eligibility and layer recommendation
- Match diagnosis to treatment, dressing, and medication
- Flag inconsistencies between visits

Your output should include:
1. What is documented correctly
2. What is missing or incorrect
3. A numbered list of issues with suggested corrections or rewording
'''
        )},
        {"role": "user", "content": image_data + "\n" + combined_text}
    ]

if st.button("Run Audit and Generate PDF") and notes:
    with st.spinner("Running audit and generating report..."):
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
    st.info("Upload 1 to 4 wound care documents and click the button to begin.")
