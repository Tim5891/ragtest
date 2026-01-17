import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import json

st.set_page_config(page_title="AI Regulatory Auditor", layout="wide")

# --- API SETUP ---
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("Please enter your Gemini API Key in the sidebar to begin.")

# --- APP UI ---
st.title("⚖️ AI-Powered Regulatory Gap Analysis")
st.markdown("Upload an enforcement notice. Gemini will extract specific failures and suggest 'Dial Fixes' for your Fraud Simulator.")

uploaded_file = st.file_uploader("Upload Enforcement Notice (PDF)", type="pdf")

if uploaded_file and api_key:
    # 1. Extract Text
    with st.spinner("Reading PDF..."):
        reader = PdfReader(uploaded_file)
        text = " ".join([page.extract_text() for page in reader.pages])

    # 2. AI Analysis Prompt
    prompt = f"""
    You are an expert Regulatory Compliance Auditor. Analyze the following enforcement notice text:
    
    {text[:10000]} 

    Identify the top 3-4 specific operational failures related to transaction monitoring or fraud.
    For each failure, provide:
    1. A short title of the violation.
    2. A brief description of what the regulator found.
    3. A 'Recommended Dial Fix' for a fraud model (choose from: 'Increase Sensitivity', 'Increase Amount Weight', or 'Increase Velocity Weight').

    Format your output ONLY as a valid JSON list of objects like this:
    [
      {{"area": "Title", "description": "Description", "fix": "Fix Name"}}
    ]
    """

    # 3. Call Gemini
    with st.spinner("Gemini is analyzing the notice for gaps..."):
        try:
            response = model.generate_content(prompt)
            # Clean the response in case Gemini adds markdown backticks
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            findings = json.loads(clean_json)

            # 4. Display findings as a Questionnaire
            st.header("📋 AI-Generated Gap Questionnaire")
            
            user_responses = []
            for i, item in enumerate(findings):
                with st.expander(f"Violation {i+1}: {item['area']}", expanded=True):
                    st.error(f"**The Regulator Found:** {item['description']}")
                    st.info(f"💡 **Suggested Simulator Fix:** {item['fix']}")
                    
                    # Interactivity
                    status = st.select_slider(
                        "Assessment:",
                        options=["Critical Gap", "Partial Gap", "Compliant"],
                        key=f"status_{i}"
                    )
                    notes = st.text_area("Remediation Plan:", key=f"notes_{i}")
                    
                    user_responses.append({"Area": item['area'], "Status": status, "Notes": notes})

            if st.button("Download Gap Report"):
                df_report = pd.DataFrame(user_responses)
                st.download_button("Export CSV", df_report.to_csv(index=False), "gap_report.csv")

        except Exception as e:
            st.error(f"Error processing AI response: {e}")
            st.write("Raw Response:", response.text)
