import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import json
import pandas as pd

st.set_page_config(page_title="Gemini 2.0 Compliance Auditor", layout="wide")

# --- API SETUP ---
st.sidebar.header("AI Configuration")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model_choice = st.sidebar.selectbox("Model Version", ["gemini-2.0-flash-exp", "gemini-2.0-pro-exp"])

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_choice)
else:
    st.warning("🔑 Enter your Gemini API Key to unlock AI analysis.")

st.title("⚖️ Gemini 2.0 Regulatory Auditor")
st.markdown("Upload a legal notice. The AI will cross-reference the findings with your Fraud Model parameters.")

uploaded_file = st.file_uploader("Upload Enforcement Notice (PDF)", type="pdf")

if uploaded_file and api_key:
    # 1. Extract Full Text (Gemini 2.0 can handle huge contexts)
    with st.spinner("Processing Document..."):
        reader = PdfReader(uploaded_file)
        full_text = " ".join([page.extract_text() for page in reader.pages])

    # 2. AI Prompt tuned for 2.0 Reasoning
    prompt = f"""
    Act as a Senior Compliance Officer. Review this enforcement notice:
    
    {full_text}

    Identify the core 'Thematic Failures' that led to the fine. 
    For each failure, provide a structured response in JSON format:
    1. 'area': The high-level risk (e.g., Velocity, High-Value, Thresholds).
    2. 'finding': What the firm did wrong.
    3. 'dial_fix': How to adjust a fraud model. Choose exactly one: ('Increase Sensitivity', 'Increase Amount Weight', 'Increase Velocity Weight').
    4. 'severity': (Low, Medium, High).

    Output ONLY a JSON list of objects.
    """

    with st.spinner("Gemini 2.0 is reasoning over the legal text..."):
        try:
            response = model.generate_content(prompt)
            # Clean JSON formatting
            raw_json = response.text.replace('```json', '').replace('```', '').strip()
            findings = json.loads(raw_json)

            st.header("📋 Gap Analysis Questionnaire")
            
            audit_results = []
            for i, item in enumerate(findings):
                with st.expander(f"{item['area']} - Severity: {item['severity']}", expanded=True):
                    st.error(f"**Regulatory Finding:** {item['finding']}")
                    st.info(f"💡 **Simulator Recommendation:** {item['dial_fix']}")
                    
                    status = st.select_slider("Internal Assessment:", 
                                            options=["Critical Gap", "Partial", "Compliant"], 
                                            key=f"status_{i}")
                    plan = st.text_area("Remediation Plan:", key=f"plan_{i}")
                    
                    audit_results.append({"Area": item['area'], "Status": status, "Plan": plan})

            # Export Capability
            if audit_results:
                csv = pd.DataFrame(audit_results).to_csv(index=False)
                st.download_button("📩 Download Audit Report", csv, "compliance_audit.csv", "text/csv")

        except Exception as e:
            st.error(f"Analysis Failed: {e}")
