
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
st.title("CMS-Grade Wound Audit Tool")

st.markdown("Upload 1–10 notes. 1 = individual audit. 2–10 = compare for consistency, compliance, and graft use.")

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
    image_context = "Image provided. Consider granulation, exudate, tissue state."

def clean_text(text):
    return (
        text.replace("•", "-").replace("–", "-").replace("—", "-")
        .replace("“", '"').replace("”", '"').replace("’", "'")
    )

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    lines = clean_text(content).splitlines()

    for line in lines:
        safe_line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, safe_line)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        return tmpfile.name

def build_prompt(notes, img="", compare=False):
    combined = "\n---\n".join(notes)
    instructions = '''You are a CMS wound documentation auditor. Use LCDs L35125, L35041, A56696.
Evaluate TIMERS, healing trajectory, infection treatment, graft use and conservative care.
Format output with:
Section 1: What is Documented Correctly
Section 2: What is Missing or Incorrect (include suggested fix under each)
Section 3: Numbered List of Issues with Suggested Rewording
Final: Compliance Rating: Compliant / Partially Compliant / Non-Compliant
'''
    if compare:
        instructions += "\nCompare notes chronologically. Assess graft continuation or discontinuation across visits."
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": img + "\n" + combined}
    ]

if st.button("Run Audit", type="primary") and notes:
    compare = len(notes) > 1
    with st.spinner("Auditing..."):
        response = client.chat.completions.create(model="gpt-4o", messages=build_prompt(notes, image_context, compare))
        output = response.choices[0].message.content
        st.markdown(output)

        path = generate_pdf(output)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Wound_Audit_Report.pdf">Download PDF Report</a>', unsafe_allow_html=True)
