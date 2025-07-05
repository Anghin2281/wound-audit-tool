
# Novitas LCD L35125 Wound Audit Tool - CMS-Compliant PDF Upload and Audit

import streamlit as st
import openai
from docx import Document
from PIL import Image
import fitz
from fpdf import FPDF
import base64
import tempfile

client = openai.OpenAI()

st.set_page_config(page_title="Novitas Wound Audit Tool - L35125", layout="wide")
st.title("🧾 Wound Documentation Auditor (Novitas LCD L35125 Only)")

st.markdown("""
Upload wound care notes and receive a detailed CMS audit strictly based on **Novitas LCD L35125** requirements.

This tool:
- Audits documentation using L35125 standards only
- Flags missing elements
- Recommends exact corrections
- Generates a provider-ready correction PDF
""")

uploaded_file = st.file_uploader("📁 Upload Wound Note (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
note_text = ""

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        pdf_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        note_text = ""
        for page in pdf_doc:
            note_text += page.get_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        note_text = "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.type == "text/plain":
        note_text = uploaded_file.read().decode("utf-8")

if not note_text:
    note_text = st.text_area("Or paste wound note text here:", height=300)

# Optional image input
image_file = st.file_uploader("Optional: Upload wound image (.jpg, .png)", type=["jpg", "jpeg", "png"])
image_context = ""
if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_context = "Note includes a wound image. Consider wound appearance and dimensions."

# L35125-specific checklist
st.markdown("### ✅ Novitas L35125 Documentation Checklist")
st.markdown("""
- [ ] Wound location, size (L×W×D) and appearance documented?
- [ ] Undermining/tunneling and exudate described?
- [ ] Wound etiology and ICD code match debridement type?
- [ ] Plan of care includes vascular, metabolic, nutritional evaluation?
- [ ] Conservative therapy trial ≥ 30 days documented?
- [ ] Frequency and clinical rationale for each debridement?
- [ ] Pre/post-wound response documented after each debridement?
- [ ] Signed and dated plan of care?
""")

def build_novitas_prompt(note: str, image_context: str = ""):
    return [
        {"role": "system", "content": (
            "You are a wound documentation compliance auditor. Review this wound note for compliance with **CMS Novitas LCD L35125** only. "
            "Check that debridement is medically necessary and supported by: size/depth/tissue status, infection signs, vascular/metabolic/nutritional evaluation, "
            "and conservative care trials. Return your response in this format:\n\n"
            "1. **Audit Summary (L35125 only)**\n"
            "2. **Missing / Incomplete Elements**\n"
            "3. **Correction Recommendations**\n"
            "4. **Suggested Wording Fixes**\n"
            "5. **Final Compliance Rating: Compliant / Partial / Non-Compliant**"
        )},
        {"role": "user", "content": image_context + "\n\n" + note}
    ]

def generate_pdf(content: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for line in content.splitlines():
        pdf.multi_cell(0, 7, line)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        return tmpfile.name

if st.button("🔍 Audit (L35125) and Generate PDF") and note_text:
    with st.spinner("Auditing for Novitas LCD L35125..."):
        messages = build_novitas_prompt(note_text, image_context)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        audit_output = response.choices[0].message.content
        st.subheader("📋 Novitas LCD L35125 Audit Report")
        st.markdown(audit_output)

        pdf_path = generate_pdf(audit_output)
        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Novitas_Wound_Audit_Report.pdf">📥 Download Correction Report (PDF)</a>'
            st.markdown(href, unsafe_allow_html=True)
else:
    st.info("Upload or paste a wound note and click 'Audit (L35125) and Generate PDF'")
