
import streamlit as st

st.set_page_config(page_title="Wound Audit Tool - Mastered Knowledge", layout="wide")
st.title("Wound Audit Tool - Mastered Capabilities Summary")

st.markdown("""## CMS & LCD GUIDELINES""")
st.markdown("""
- LCD L35125 (Novitas)  
- LCD L35041 (CGS)  
- Article A56696 (Billing/Coding for Skin Substitutes)  
- LCD L39865 explicitly excluded  
""")

st.markdown("""## WOUND CARE FRAMEWORKS""")
st.markdown("""**TIMERS Framework:**  
- Tissue: granulation, slough, necrosis, debridement  
- Infection/Inflammation: erythema, odor, exudate, antibiotics  
- Moisture: exudate type/amount, dressing selection  
- Edge: epibole, undermining, migration  
- Regeneration: granulation percentage, epithelialization, graft application  
- Social: caregiver support, compliance, education  
""")

st.markdown("""**Measurable Outcomes / Healing Trajectory:**  
- Wound area and volume (L x W x D)  
- Compares percentage area reduction across 2–4 notes  
- Flags if less than 30 percent improvement in 4 weeks  
""")

st.markdown("""**Wound Management Protocols:**  
- Dressing selection based on wound type  
- Conservative treatment for more than 30 days  
- Graft justification requirements  
""")

st.markdown("""## GRAFT LOGIC""")
st.markdown("""- Graft eligibility based on wound chronicity, healing percentage, conservative care  
- Graft layer recommendation:  
  - Single / double / triple / quadruple layer  
  - Based on wound depth, size, exudate level  
- Matches graft use to documented trajectory  
""")

st.markdown("""## INFECTION & MEDICATION MATCHING""")
st.markdown("""- Detects infection (e.g., cellulitis, purulence)  
- Verifies antibiotic or antiseptic documentation  
- Flags mismatches or missing treatment  
- Ensures diagnosis-treatment-prescription alignment  
""")

st.markdown("""## DOCUMENTATION STANDARDS""")
st.markdown("""- Conservative care duration and progress  
- ICD-10 and CPT inclusion  
- Plan of care documentation  
- Wound response to treatment  
- Avoidance of copy-paste or cloned notes  
""")

st.markdown("""## PDF AUDIT REPORT FORMAT""")
st.markdown("""Each audited note includes:  
- File Name  
- Patient Name  
- Visit Date  
- Provider  
- Facility  
Sections in report:  
1. What is documented correctly  
2. What is missing or insufficient  
3. Numbered list of documentation issues with suggested fixes  
""")

st.markdown("""## MULTI-DOCUMENT AUDITING""")
st.markdown("""- Accepts 1 to 4 notes per audit  
- Tracks wound consistency across visits  
- Calculates healing percentage and trajectory  
- Compares documentation completeness per visit  
""")

st.markdown("""## TECHNICAL FEATURES""")
st.markdown("""- File support: PDF, DOCX, TXT  
- Optional image upload: JPG, PNG  
- Unicode-safe PDF generation  
- Clean text format (no emojis or symbols)  
- Runs in Streamlit  
- One-click downloadable audit report  
""")
