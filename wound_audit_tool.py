import streamlit as st
import openai
from docx import Document
from PIL import Image
import fitz
from fpdf import FPDF
import tempfile
import base64
import re
import pandas as pd

client = openai.OpenAI()

st.set_page_config(page_title="CMS LCD-Based Wound Audit Tool", layout="wide")
st.markdown("<h1 style='color:#800000'>Strict CMS LCD Wound Audit Tool</h1>", unsafe_allow_html=True)

st.markdown("This tool audits wound documentation against CMS LCDs: L35125, L35041, A56696, L37228, L37166, L33831, and article A58565.")

uploaded_files = st.file_uploader("Upload 1–10 Wound Notes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
image_file = st.file_uploader("Optional Wound Image", type=["jpg", "jpeg", "png"])

notes = []
note_info_headers = []
note_summary = []
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
        p_val = patient.group(0).strip() if patient else "Unknown"
        d_val = date.group(0).strip() if date else "Unknown"
        pr_val = provider.group(0).strip() if provider else "Unknown"
        f_val = facility.group(0).strip() if facility else "Unknown"

        header.append(f"Patient: {p_val}")
        header.append(f"Date of Visit: {d_val}")
        header.append(f"Provider: {pr_val}")
        header.append(f"Facility: {f_val}")

        note_info_headers.append("\n".join(header))
        note_summary.append([file.name, p_val, d_val, pr_val, f_val])

        notes.append(content + "\n" + raw)

image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Wound Image Uploaded", use_column_width=True)
    image_context = "Image uploaded. Consider granulation, exudate, periwound status."

def clean_text(text):
    return text.replace("•", "-").replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"').replace("’", "'")

def generate_combined_pdf(summary_df, audit_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, "Audit Summary:")
    pdf.ln(5)
    pdf.add_page()
    for line in clean_text(audit_text).splitlines():
        safe = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, safe)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

def build_prompt(notes, img="", compare=False, headers=None):
    combined = "\n---\n".join(notes)
    header_text = "\n\n".join(headers) if headers else ""
    instructions = """You are a strict CMS wound documentation auditor using the following guidelines:
- LCD L35125 (Novitas)
- LCD L35041 (Novitas)
- A56696 (Billing/Coding for L35041)
- LCD L37228 (WPS)
- LCD L37166 (First Coast)
- LCD L33831 (Surgical Dressings)
- A58565 (Palmetto Wound and Ulcer Care Article)

Your job is to:
- Detect exact compliance or missing data
- Highlight violations of CMS documentation standards
- Flag failure to meet healing thresholds (<30–50% in 4 weeks)
- Identify incorrect or missing:
  - Debridement type, justification, depth, and tools
  - Wound dimensions, drainage, pain, necrosis, tunneling, exudate
  - SMART goals and measurable progress
  - Use and documentation of biophysical modalities (MIST, NPWT, ES)
  - Dressing appropriateness (e.g., hydrogel on eschar)
  - Therapist documentation (every 10 days)
  - Pre/post photos for prolonged debridement
  - Clear medical necessity and plan modifications if no healing occurs
  - Pathology reports when deep tissue removed

If multiple notes are uploaded:
- Evaluate consistency across all notes
- Highlight contradictions in wound progression, debridement details, documentation standards, or care plans
- Identify where updates are needed for consistency
- Provide examples from other notes that are compliant or inconsistent
- Offer suggestions to make all notes aligned and CMS-compliant
- Output a visual table of consistency by category if appropriate

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
- Labeled by category (e.g., Debridement, Dressing, Biophysical Modalities)
- What is wrong
- Why it's non-compliant (with LCD/article reference if possible)

Section 3: Suggested Fixes and CMS Justified Corrections
1. Problem – Suggested Rewording
2. ...

Section 4: Inconsistencies Between Notes
- What is inconsistent
- Example of note(s) that meet standard
- Example of note(s) that fall short
- How to harmonize and resolve differences
- Highlight these areas clearly for provider revision

Section 5: Final CMS Compliance Rating (Compliant / Partially Compliant / Non-Compliant)
====="""
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

        combined_pdf_path = generate_combined_pdf(pd.DataFrame(note_summary, columns=["File Name", "Patient", "Date of Visit", "Provider", "Facility"]), result)
        with open(combined_pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Combined_Wound_Audit_Report.pdf">Download Combined PDF Report</a>', unsafe_allow_html=True)
