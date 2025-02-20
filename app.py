import streamlit as st
import toml
from utils import (
    summarize_resume,
    summarize_requirements,
    analyze_alignment,
    extract_percentage,
    load_pdf_text,
    ats_score
)

# Load configuration
config = toml.load(".streamlit/config.toml")
max_size_mb = st.config.get_option("server.maxUploadSize")
st.set_page_config(page_title="CareerFit-AI" , page_icon="🎯")

st.title("🎯 CareerFit-AI")
st.subheader("AI-Powered Job Fit Analyzer")

# Create tabs
tab1, tab2 = st.tabs(["🔍 ATS checker", "📈 Job Alignment"])

# ATS Check Tab
with tab1:
    st.header("ATS Resume shecker")
    ats_resume = st.file_uploader(f"Upload your Resume here (Max {max_size_mb}MB)", type=["pdf", "docx"])

    if st.button("Check ATS score"):
        if ats_resume:
            if ats_resume.size > 10 * 1024 * 1024:
                st.warning("File must be less than 10 MB.")
            else:
                with st.spinner('Analyzing ATS compatibility...'):
                    # Load resume text
                    resume_text = load_pdf_text(ats_resume)
                    resume_summary = summarize_resume(resume_text)
                    
                    # Get ATS analysis
                    ats_analysis = ats_score(resume_summary)
                    
                    st.subheader("ATS Analysis Results")
                    st.write(ats_analysis)
                    st.write("Note: Results are based on general ATS compatibility guidelines.")
                    
                    resume_summary = ""
                    ats_analysis = ""
        else:
            st.warning("Please upload a resume to analyze.")
    

# Job Alignment Tab
with tab2:
    st.header("Job Alignment")
    # File uploaders for resume and requirements
    resume_file = st.file_uploader(f"Upload your Resume (Max {max_size_mb}MB)", type=["pdf", "docx"])
    requirements_file = st.file_uploader("Upload Job Requirements", type=["pdf", "txt"], accept_multiple_files=False)
    extra_instructions = st.text_area("Additional Instructions or Context (Optional)", 
        help="Add any specific points or context you want the analysis to focus on")

    # Button to trigger analysis
    if st.button("Analyze..."):
        if resume_file and requirements_file:
            if resume_file.size > 10 * 1024 * 1024 or requirements_file.size > 10 * 1024 * 1024:
                st.warning("Each file must be less than 10 MB.")
            else:
                with st.spinner('Analyzing the documents...'):
                    # Load resume text
                    resume_text = load_pdf_text(resume_file)

                    # Load requirements text
                    if requirements_file.type == "application/pdf":
                        requirements_text = load_pdf_text(requirements_file)
                    else:
                        requirements_text = requirements_file.getvalue().decode("utf-8")

                    # Summarize resume and requirements
                    resume_summary = summarize_resume(resume_text)
                    requirements_summary = summarize_requirements(requirements_text)

                    # Compare summaries
                    alignment_result = analyze_alignment(resume_summary, requirements_summary, extra_instructions)

                    # Extract and display the overall fit percentage
                    fit_percentage = extract_percentage(alignment_result)
                    if fit_percentage is not None:
                        st.subheader(f"Overall Fit: {fit_percentage}%")

                    st.subheader("Alignment Analysis")
                    st.write(alignment_result)
                    st.write("Results may vary based on the resume and job requirements.")
                    
                    resume_summary = ""
                    requirements_summary = ""
                    alignment_result = ""
                    fit_percentage = ""
                    
        else:
            st.warning("Please upload both the resume and job requirements.")
