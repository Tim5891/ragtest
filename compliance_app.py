import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import time
import os

st.set_page_config(page_title="Gemini 2.0 Auditor", layout="wide")

# --- API SETUP ---
st.sidebar.header("AI Configuration")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Using Gemini 2.0 Flash for speed and high context
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
else:
    st.warning("🔑 Enter your Gemini API Key in the sidebar to begin.")

st.title("⚖️ Gemini 2.0 Regulatory Auditor")
st.markdown("Upload an enforcement notice. Gemini 2.0 will 'read' the document directly, bypassing encryption issues.")

uploaded_file = st.file_uploader("Upload Enforcement Notice (PDF)", type="pdf")

if uploaded_file and api_key:
    # 1. Save and Upload to Google File API
    with st.spinner("Uploading to Gemini 2.0..."):
        # Temporary save for the API to pick up
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Native PDF Upload
        sample_file = genai.upload_file(path=temp_path, mime_type="application/pdf")
        
        # Delete temp file from local storage
        os.remove(temp_path)

    # 2. Wait for Processing
    # Files are often in a 'PROCESSING' state for a few seconds
    while sample_file.state.name == "PROCESSING":
        time.sleep(2)
        sample_file = genai.get_file(sample_file.name)

    # 3. AI Analysis Prompt
    prompt = """
    Identify the top 4 specific operational or 'Transaction Monitoring' failures in this document.
    For each failure, output a JSON object with:
    - 'area': High-level failure name.
    - 'reasoning': Why the regulator was upset.
    - 'severity': High, Medium, or Low.
    - 'dial_fix': One of ('Increase Sensitivity', 'Increase Amount Weight', 'Increase Velocity Weight').

    Format the final output as a JSON list.
    """

    with st.spinner("AI is reasoning over the document..."):
        try:
            # Send file object + prompt
            response = model.generate_content([sample_file, prompt])
            
            # Parse JSON
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            findings = json.loads(raw_text)

            st.header("📋 AI-Generated Gap Questionnaire")
            
            audit_data = []
            for i, item in enumerate(findings):
                with st.expander(f"Violation: {item['area']} ({item['severity']})", expanded=True):
                    st.error(f"**Regulatory Finding:** {item['reasoning']}")
                    st.info(f"💡 **Suggested Fix:** {item['dial_fix']}")
                    
                    # Manual user input for the 'Gap Analysis'
                    status = st.select_slider("Assessment:", 
                                            options=["Critical Gap", "Partial Gap", "Compliant"], 
                                            key=f"status_{i}")
                    plan = st.text_area("Remediation Plan:", key=f"plan_{i}")
                    
                    audit_data.append({"Area": item['area'], "Status": status, "Plan": plan})

            # 4. Clean up file from Google Cloud (good practice)
            genai.delete_file(sample_file.name)

            # Export Report
            if audit_data:
                df_report = pd.DataFrame(audit_data)
                st.download_button("📩 Download Final Audit Report", df_report.to_csv(index=False), "gap_analysis.csv")

        except Exception as e:
            st.error(f"Analysis Failed: {e}")
            if 'response' in locals():
                st.write("Raw AI Output:", response.text)
