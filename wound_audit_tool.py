
# CMS-Compliant Wound Audit Tool with Healing Trajectory and Risk Score

import streamlit as st
import openai
from docx import Document
from PIL import Image
import fitz
from fpdf import FPDF
import base64
import tempfile
import re

client = openai.OpenAI()

st.set_page_config(page_title="CMS Wound Audit Tool with Healing & Risk Score", layout="wide")
st.title("CMS-Grade Wound Note Auditor (L35125 + L38902 + Healing Score)")

st.markdown("""
This AI tool audits wound care documentation for CMS compliance and calculates:
- 📉 Healing Trajectory (surface area improvement)
- ⚠️ Wound Risk Score (based on exudate, depth, periwound, and history)

It uses LCD L35125 (Novitas) and L38902 (Noridian) as the audit framework.
""")

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

st.markdown("### Optional: Upload Wound Image")
image_file = st.file_uploader("Upload Image (.jpg, .png)", type=["jpg", "jpeg", "png"])
image_info = ""

if image_file is not None:
    image = Image.open(image_file)
    st.image(image, caption="Uploaded Wound Image", use_column_width=True)
    image_info = "Wound image provided. AI should consider wound size, shape, and appearance."

st.markdown("### ✅ CMS Smart Checklist")
st.markdown("""
- [ ] Location, size, depth, undermining/tunneling documented?
- [ ] Drainage type and amount?
- [ ] Conservative care documented for ≥ 30 days?
- [ ] ICD-10 and CPT codes accurate and match wound type?
- [ ] Plan of care includes vascular and nutrition assessment?
- [ ] Wound showing measurable signs of healing?
- [ ] Skin substitute justification present?
- [ ] Debridement code type supported (selective/non-selective/surgical)?
- [ ] Granulation tissue or surface dimension improvement?
""")

def extract_wound_data(text):
    wounds = re.findall(r"Measurement: (\d+(\.\d+)?) x (\d+(\.\d+)?) cm x (\d+(\.\d+)?)", text)
    surface_areas = re.findall(r"Surface Area: (\d+(\.\d+)?)", text)
    drainage = len(re.findall(r"Drainage/Exudate: Yes", text))
    tunneling = len(re.findall(r"Tunneling: Yes", text))
    periwound_red = len(re.findall(r"Periwound Skin: .*redness", text, re.IGNORECASE))
    return wounds, surface_areas, drainage, tunneling, periwound_red

def calculate_healing_trend(surface_areas):
    try:
        areas = [float(a[0]) for a in surface_areas]
        if len(areas) >= 2:
            change = ((areas[-2] - areas[-1]) / areas[-2]) * 100
            return round(change, 2)
    except:
        pass
    return None

def calculate_risk_score(drainage_count, tunneling_count, periwound_red_count):
    score = 0
    score += drainage_count * 2
    score += tunneling_count * 3
    score += periwound_red_count * 2
    if score == 0:
        return "Low Risk"
    elif score <= 5:
        return "Moderate Risk"
    else:
        return "High Risk"

def build_audit_prompt(note: str, image_context: str = ""):
    return [
        {"role": "system", "content": (
            "You are a CMS wound care compliance auditor. Review this wound care note for accuracy, completeness, "
            "and LCD compliance based on L35125 and L38902. Check for medical necessity, healing progression, conservative care, "
            "proper CPT/ICD use, vascular/nutritional status, and wound progression. Format output as:\n\n"
            "1. **Audit Summary**\n2. **Recommendations**\n3. **Corrected Note**\n4. **Compliance Rating**"
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

if st.button("Run CMS Audit and Export PDF") and note_text:
    with st.spinner("Auditing note, checking healing trend, and calculating risk score..."):
        wounds, surface_areas, drainage_count, tunneling_count, periwound_red_count = extract_wound_data(note_text)
        healing_pct = calculate_healing_trend(surface_areas)
        risk = calculate_risk_score(drainage_count, tunneling_count, periwound_red_count)

        messages = build_audit_prompt(note_text, image_info)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        audit_output = response.choices[0].message.content

        if healing_pct is not None:
            st.success(f"📉 Healing Trajectory: {healing_pct}% surface area reduction")
        else:
            st.warning("⚠️ Healing Trajectory: Not enough data to calculate.")

        st.info(f"⚠️ Wound Risk Score: {risk}")
        st.subheader("CMS Audit Results (L35125 / L38902)")
        st.markdown(audit_output)

        # Create combined report
        full_report = f"Healing Trajectory: {healing_pct if healing_pct else 'N/A'}%\nRisk Score: {risk}\n\n" + audit_output
        pdf_path = generate_pdf(full_report)

        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="CMS_Wound_Audit_Report.pdf">📥 Download PDF Report</a>'
            st.markdown(href, unsafe_allow_html=True)
else:
    st.info("Upload or paste a wound care note and click 'Run CMS Audit and Export PDF'.")
