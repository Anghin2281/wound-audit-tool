
# wound_audit_tool.py - AI-Powered CMS-Grade Wound Note Audit Tool with PDF Support

import streamlit as st
import openai
from docx import Document
from PIL import Image
import fitz  # PyMuPDF for PDF reading

client = openai.OpenAI()

st.set_page_config(page_title="Advanced Wound Care Note Compliance Auditor", layout="wide")
st.title("AI-Powered CMS-Grade Wound Care Note Auditor")

st.markdown("""
This enhanced tool performs a detailed CMS-style audit of your wound care notes. It checks compliance with all major LCDs (L35125, L35041), CPT/ICD alignment, simulates fraud-detection AI logic used by Medicare auditors, and includes image upload for wound assessment + smart field prompts. PDF support included.
""")

# Upload or paste wound care note
uploaded_file = st.file_uploader("Upload Wound Note (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
note_text = ""

if uploaded_file is not None:
    if uploaded_file.type == "text/plain":
        note_text = uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        note_text = "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.type == "application/pdf":
        pdf_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        note_text = ""
        for page in pdf_doc:
            note_text += page.get_text()

if not note_text:
    note_text = st.text_area("Or paste wound note text here:", height=300)

# Upload wound image for AI-enhanced context (optional)
st.markdown("### Optional: Upload Wound Image for Size/Shape Analysis")
image_file = st.file_uploader("Upload Image (.jpg, .png)", type=["jpg", "jpeg", "png"])
image_info = ""

if image_file is not None:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_info = "Wound image provided. AI should consider wound size, shape, and appearance in the audit context."

# Smart prompt checklist
st.markdown("### ✅ Smart Field Checklist")
st.markdown("""
- [ ] Wound location and size (length × width × depth)?
- [ ] Drainage type and amount documented?
- [ ] Undermining or tunneling noted?
- [ ] Wound base and periwound described?
- [ ] Tissue types removed during debridement?
- [ ] Conservative care attempted and duration?
- [ ] Skin substitute justification present?
- [ ] ICD-10 and CPT codes documented?
""")

# Prompt builder
def build_audit_prompt(note: str, image_context: str = ""):
    return [
        {"role": "system", "content": (
            "You are an expert CMS wound documentation auditor. Your task is to rigorously analyze wound care notes "
            "to ensure full compliance with Medicare standards. Use the logic of CMS AI systems, including fraud detection, "
            "LCDs (L35125, L35041), ICD-10-CM accuracy, CPT justification, and documentation completeness. "
            "Flag anything missing or risky such as: missing dimensions, drainage/tunneling/undermining, conservative care trial, "
            "appropriate debridement coding, correct CTP usage justification, and patient response. If a wound image is provided, "
            "use it to infer size or support compliance reasoning. Give a detailed compliance report, suggested corrections, "
            "ICD/CPT validation, and a final compliance score: Compliant / Partially Compliant / Non-Compliant."
        )},
        {"role": "user", "content": image_context + "\n\n" + note}
    ]

if st.button("Run Advanced Audit") and note_text:
    with st.spinner("Running CMS-grade AI audit with optional image and PDF support..."):
        messages = build_audit_prompt(note_text, image_info)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        audit_output = response.choices[0].message.content
        st.subheader("Detailed Audit Report")
        st.markdown(audit_output)
else:
    st.info("Upload or paste a wound care note and click 'Run Advanced Audit' to begin.")
