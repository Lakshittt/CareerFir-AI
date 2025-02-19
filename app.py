import os
from dotenv import load_dotenv
import toml
import streamlit as st
import google.generativeai as genai
import tempfile
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from typing import Any, List, Optional, Mapping
from pydantic import Field, model_validator
from pydantic.config import ConfigDict
import re

# Load configuration
config = toml.load(".streamlit/config.toml")
max_size_mb = st.config.get_option("server.maxUploadSize")

# Load and configure Gemini
dotenv_path = ".env"
load_dotenv(dotenv_path)
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError(f"Unable to retrieve GEMINI_API_KEY from {dotenv_path}")

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

# Function to summarize text using Gemini
def summarize_text(text):
    prompt = f"Please summarize the following text concisely:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

# Function to analyze resume alignment
def analyze_alignment(resume_text, requirements_text, extra_instructions):
    prompt = (
        f"**Objective:** Perform a thorough and structured analysis of the candidate's resume against the given job description to determine their suitability for the role.\n\n"
        f"**Instructions:**\n"
        f"1. **Resume Summary:** Provide a well-structured summary of the candidate's qualifications, skills, and work experience. Highlight notable achievements, certifications, and technical expertise.\n"
        f"2. **Alignment Analysis:** Compare the candidate's profile with the job requirements in detail:\n"
        f"   - Identify key strengths that align with the role.\n"
        f"   - Highlight specific skills, technologies, or experiences that match the job description, using direct references from the resume.\n"
        f"   - Evaluate relevant projects, roles, or industry exposure.\n"
        f"3. **Gaps & Areas of Improvement:**\n"
        f"   - Identify missing or weak areas where the candidate does not fully meet the job requirements.\n"
        f"   - Provide clear and actionable recommendations to bridge these gaps, such as acquiring certain skills, certifications, or work experience.\n"
        f"4. **Fit Percentage Calculation:** Assign a fit percentage (0-100) based on how well the candidate's profile aligns with the job requirements. Justify this score with:\n"
        f"   - A breakdown of how each major requirement is met.\n"
        f"   - Weighting factors for experience, technical expertise, and industry relevance.\n"
        f"   - A reasoned explanation behind the final score, ensuring a conservative and objective assessment.\n"
        f"5. **Final Recommendation:** Summarize the overall fit of the candidate:\n"
        f"   - Clearly state whether the candidate is a strong match, a moderate fit with areas for improvement, or not a suitable match.\n"
        f"   - Provide a short concluding statement with the primary reason for the recommendation.\n\n"
        f"**Data Blocks:**\n"
        f"**Candidate Resume:**\n{resume_text}\n\n"
        f"**Job Requirements:**\n{requirements_text}\n\n"
        f"**Output Format:**\n"
        f"- Use clear section headings for readability.\n"
        f"- Present comparisons and analysis in bullet points or tables where applicable.\n"
        f"- Ensure the final output includes a 'Fit Percentage' and a 'Final Recommendation' section.\n"
        f"- Keep the insights concise, relevant, and actionable.\n\n"
        f"**Additional Instructions:**\n{extra_instructions}\n\n"
    )
    response = model.generate_content(prompt)
    return response.text

# Function to summarize resume
def summarize_resume(resume_text):
    prompt = (
        f"**Objective:** Generate a concise and structured summary of the candidate's resume, focusing on key aspects relevant to a job application.\n\n"
        f"**Instructions:**\n"
        f"1. **Professional Summary:** Provide a high-level overview of the candidate's background, including total years of experience and industry expertise.\n"
        f"2. **Key Skills & Technologies:** List the primary technical and soft skills mentioned in the resume.\n"
        f"3. **Work Experience:** Summarize the most relevant job roles and responsibilities, emphasizing achievements, leadership roles, and industry contributions.\n"
        f"4. **Certifications & Education:** Highlight degrees, certifications, and relevant training programs.\n"
        f"5. **Notable Projects & Contributions:** Mention any major projects, open-source contributions, or research work if applicable.\n\n"
        f"**Candidate Resume:**\n{resume_text}\n\n"
        f"**Output Format:**\n"
        f"- Use bullet points or a structured format for clarity.\n"
        f"- Focus on concise but impactful insights.\n"
        f"- Ensure the summary highlights the most critical qualifications relevant to a job search.\n"
    )
    response = model.generate_content(prompt)
    return response.text

# Function to summarize requirements
def summarize_requirements(requirements_text):
    prompt = (
        f"**Objective:** Provide a well-structured and concise summary of the job requirements, focusing on the key criteria for candidate evaluation.\n\n"
        f"**Instructions:**\n"
        f"1. **Job Title & Summary:** Extract the job title and provide a brief description of the role's primary purpose.\n"
        f"2. **Key Skills & Technologies Required:** List essential technical and soft skills necessary for the position.\n"
        f"3. **Experience Level:** Specify the required years of experience and any industry-specific expectations.\n"
        f"4. **Educational Qualifications:** Summarize the degree, certifications, or training requirements.\n"
        f"5. **Responsibilities & Expectations:** Highlight the primary duties and expectations for the candidate.\n"
        f"6. **Preferred Qualifications (if any):** Mention additional desirable skills, certifications, or industry knowledge.\n\n"
        f"**Job Description:**\n{requirements_text}\n\n"
        f"**Output Format:**\n"
        f"- Present the summary in a structured format with headings and bullet points.\n"
        f"- Focus on extracting the most critical and relevant details.\n"
        f"- Keep the summary concise while ensuring all major requirements are covered.\n"
    )
    response = model.generate_content(prompt)
    return response.text

# Function to extract percentage from the response
def extract_percentage(alignment_result):
    sections = alignment_result.split('\n\n')
    for section in sections:
        if 'fit percentage' in section.lower():
            match = re.search(r'(?:fit percentage|alignment):\s*(\d{1,3})%', section, re.IGNORECASE)
            if match:
                percentage = int(match.group(1))
                if 0 <= percentage <= 100:
                    return percentage
    return None

# Initialize text splitter
text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=800,
    chunk_overlap=200,
    length_function=len,
)

# Streamlit application title
st.title("🎯 AI-Powered Job Fit Assessment")

# File uploaders for resume and requirements
resume_file = st.file_uploader(f"Upload your Resume (Max {max_size_mb}MB)", type=["pdf"])
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
                with tempfile.NamedTemporaryFile(delete=False) as tmp_resume:
                    tmp_resume.write(resume_file.read())
                    resume_loader = PyPDFLoader(tmp_resume.name)
                    resume_text = ''.join([p.page_content for p in resume_loader.load_and_split()])

                # Load requirements text
                if requirements_file.type == "application/pdf":
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_requirements:
                        tmp_requirements.write(requirements_file.read())
                        requirements_loader = PyPDFLoader(tmp_requirements.name)
                        requirements_text = ''.join([p.page_content for p in requirements_loader.load_and_split()])
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
    else:
        st.warning("Please upload both the resume and job requirements.")
