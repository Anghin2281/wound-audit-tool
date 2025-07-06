
# Wound Audit Tool - Mastered Capabilities Summary (Plain Text Format)

This module outlines all knowledge, frameworks, and clinical standards mastered and integrated into the Wound Documentation Audit Tool.

========================
CMS & LCD GUIDELINES
========================
- LCD L35125 (Novitas)
- LCD L35041 (CGS)
- Article A56696 (Billing/Coding for Skin Substitutes)
- LCD L39865 explicitly excluded

========================
WOUND CARE FRAMEWORKS
========================
TIMERS Framework:
- Tissue: granulation, slough, necrosis, debridement
- Infection/Inflammation: erythema, odor, exudate, antibiotics
- Moisture: exudate type/amount, dressing selection
- Edge: epibole, undermining, migration
- Regeneration: granulation percentage, epithelialization, graft application
- Social: caregiver support, compliance, education

Measurable Outcomes / Healing Trajectory:
- Wound area and volume (L x W x D)
- Compares percentage area reduction across 2–4 notes
- Flags if less than 30 percent improvement in 4 weeks

Wound Management Protocols:
- Dressing selection based on wound type
- Conservative treatment for more than 30 days
- Graft justification requirements

========================
GRAFT LOGIC
========================
- Graft eligibility based on wound chronicity, healing percentage, conservative care
- Graft layer recommendation:
  - Single / double / triple / quadruple layer
  - Based on wound depth, size, exudate level
- Matches graft use to documented trajectory

========================
INFECTION & MEDICATION MATCHING
========================
- Detects infection (e.g., cellulitis, purulence)
- Verifies antibiotic or antiseptic documentation
- Flags mismatches or missing treatment
- Ensures diagnosis-treatment-prescription alignment

========================
DOCUMENTATION STANDARDS
========================
- Conservative care duration and progress
- ICD-10 and CPT inclusion
- Plan of care documentation
- Wound response to treatment
- Avoidance of copy-paste or cloned notes

========================
PDF AUDIT REPORT FORMAT
========================
- Includes for each note:
  - File Name
  - Patient Name
  - Visit Date
  - Provider
  - Facility
- Report Sections:
  1. What is documented correctly
  2. What is missing or insufficient
  3. Numbered list of documentation issues with suggested fixes

========================
MULTI-DOCUMENT AUDITING
========================
- Accepts 1 to 4 notes per audit
- Tracks wound consistency across visits
- Calculates healing percentage and trajectory
- Compares documentation completeness per visit

========================
TECHNICAL FEATURES
========================
- File support: PDF, DOCX, TXT
- Optional image upload: JPG, PNG
- Unicode-safe PDF generation
- Clean text format (no emojis or symbols)
- Runs in Streamlit
- One-click downloadable audit report

