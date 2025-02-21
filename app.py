import streamlit as st
import toml
from utils import (
    summarize_resume,
    summarize_requirements,
    analyze_alignment,
    extract_percentage,
    load_pdf_text,
    ats_score,
    generate_linkedin_search_url,
    generate_cover_letter
)
import os

os.getenv("GEMINI_API_KEY")

# Load configuration
config = toml.load(".streamlit/config.toml")
max_size_mb = st.config.get_option("server.maxUploadSize")
st.set_page_config(page_title="CareerFit-AI" , page_icon="🎯")

st.markdown("<h1 style='margin-top: -1em;'>🎯 CareerFit-AI</h1>", unsafe_allow_html=True)
st.subheader("AI-Powered Job Fit Analyzer")

# File uploader for resume, placed outside the tabs
st.subheader("Upload Your Resume")
resume_file = st.file_uploader(
    f"Upload your Resume (Max {max_size_mb}MB)", 
    type=["pdf", "docx"], 
    key="main_resume_uploader"
)

# Process the uploaded resume and store the summary in session state
if resume_file:
    resume_text = load_pdf_text(resume_file)
    resume_summary = summarize_resume(resume_text)
    st.session_state['resume_summary'] = resume_summary

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 **ATS checker**", "📈 **Job Alignment**", "📝 **Cover Letter Generator**", "💼 **Job Search**"])

# ATS Check Tab
with tab1:
    st.subheader("ATS Resume Checker")
    if 'resume_summary' in st.session_state:
        resume_summary = st.session_state['resume_summary']
        if st.button("Check ATS score", key="ats_check_button"):
            with st.spinner('Analyzing ATS compatibility...'):
                # Get ATS analysis using the summarized resume
                ats_analysis = ats_score(resume_summary)
                
                st.subheader("ATS Analysis Results")
                st.write(ats_analysis)
                st.write("Note: Results are based on general ATS compatibility guidelines.")
    else:
        st.warning("Please upload a resume to analyze.")
    

# Job Alignment Tab
with tab2:
    st.subheader("Job Alignment")
    if 'resume_summary' in st.session_state:
        resume_summary = st.session_state['resume_summary']
        requirements_file = st.file_uploader(
            "Upload Job Requirements", 
            type=["pdf", "txt"], 
            accept_multiple_files=False, 
            key="alignment_requirements_uploader"
        )
        extra_instructions = st.text_area(
            "Additional Instructions or Context (Optional)", 
            help="Add any specific points or context you want the analysis to focus on",
            key="alignment_instructions"
        )

        if st.button("Analyze...", key="alignment_analyze_button"):
            if requirements_file:
                if requirements_file.size > 10 * 1024 * 1024:
                    st.warning("File must be less than 10 MB.")
                else:
                    with st.spinner('Analyzing the documents...'):
                        # Load requirements text
                        if requirements_file.type == "application/pdf":
                            requirements_text = load_pdf_text(requirements_file)
                        else:
                            requirements_text = requirements_file.getvalue().decode("utf-8")

                        # Summarize requirements
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
            else:
                st.warning("Please upload the job requirements.")
    else:
        st.warning("Please upload a resume to analyze.")
            

# Cover Letter Generator Tab
with tab3:
    st.subheader("AI-generated cover letter based on resume and job description.")
    if 'resume_summary' in st.session_state:
        resume_summary = st.session_state['resume_summary']
        job_description = st.text_area("Enter the job description", height=100)
        additional_instructions = st.text_area("Enter any additional instructions", height=20)
        if st.button("Generate Cover Letter", key="cover_letter_generate_button"):
            with st.spinner('Generating cover letter...'):
                cover_letter = generate_cover_letter(resume_summary, job_description, additional_instructions)
                st.subheader("Generated Cover Letter")
                st.write(cover_letter)
        # Additional functionality for cover letter generation can be added here
    else:
        st.warning("Please upload a resume to generate a cover letter.")

# Job Search Tab
with tab4:
    st.subheader("Auto-suggest jobs matching the resume.")
    if 'resume_summary' in st.session_state:
        resume_summary = st.session_state['resume_summary']
        
        if st.button("Find Jobs", key="linkedin_job_search_button"):
            with st.spinner('Generating LinkedIn job search URL...'):
                linkedin_url = generate_linkedin_search_url(resume_summary)
                st.write("Visit the following link to search for jobs on LinkedIn:")
                st.link_button("Go to LinkedIn", linkedin_url)
    else:
        st.warning("Please upload a resume to search for jobs.")
        