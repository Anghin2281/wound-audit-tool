
import streamlit as st

st.set_page_config(page_title="Wound Audit Tool Capabilities", layout="wide")
st.title("CMS Wound Audit Tool – Feature Summary")

st.markdown("### 1. Upload Capabilities")
st.markdown("""
- Upload **1 to 10 wound documentation files**
- Accepts `.pdf`, `.docx`, `.txt`
- Optional wound image upload (`.jpg`, `.jpeg`, `.png`)
- Extracts and displays:
  - Patient Name
  - Date of Visit
  - Provider
  - Facility
  - File Name
""")

st.markdown("### 2. Dual-Mode Audit Logic")
st.markdown("""
- **1 file** → individual audit  
- **2–10 files** → comparison audit:
  - Chronological consistency
  - Healing trajectory
  - CMS compliance over time
""")

st.markdown("### 3. Audit Frameworks")
st.markdown("""
- LCDs:
  - L35125 (Novitas)
  - L35041 (CGS)
  - A56696 Article
  - Excludes DL39865
- TIMERS framework:
  - Tissue
  - Infection
  - Moisture
  - Edge
  - Regeneration
  - Social
- Conservative Care: 30+ day check
- Healing trajectory: Wound % change in size
""")

st.markdown("### 4. Graft Application Checks")
st.markdown("""
- Conservative care tracking
- Healing plateau verification
- Graft layer recommendations (1-4 layers)
""")

st.markdown("### 5. Infection & Medication Validation")
st.markdown("""
- Detects infection mentions
- Validates antibiotic/antiseptic documentation
- Checks for diagnosis-treatment-prescription match
""")

st.markdown("### 6. Audit Output Format")
st.code("""
===== NOTE X =====
File Name: ...
Patient Name: ...
Date of Visit: ...
Provider: ...
Facility: ...

===== AUDIT REPORT STRUCTURE START =====
Section 1: What is Documented Correctly
Section 2: What is Missing or Insufficient
Section 3: Numbered Corrections and Suggested Fixes
===== AUDIT REPORT STRUCTURE END =====
""")

st.markdown("### 7. PDF Export")
st.markdown("""
- Unicode-safe clean formatting
- Sectioned report
- No emojis or icons
- Downloadable with one click
""")

st.markdown("### 8. User Interface")
st.markdown("""
- Streamlit interface
- Red 'Run Audit' button
- Image preview for wound photos
- Easy to read and navigate
""")
