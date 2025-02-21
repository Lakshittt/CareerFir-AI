import streamlit as st
import toml
import os
import tempfile
import re
import google.generativeai as genai
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
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

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError(f"Unable to retrieve GEMINI_API_KEY.")

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')
# Function Definitions
def summarize_text(text):
    prompt = f"Please summarize the following text concisely:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

def ats_score(ats_resume):
    prompt = (
        f"Objective: Analyze the uploaded resume with an in-depth Applicant Tracking System (ATS) evaluation. "
        f"Provide a detailed ATS compatibility score based on keyword optimization, formatting, readability, structuring, and job relevance. "
        f"Identify strengths, weaknesses, and actionable improvements for better ATS performance.\n\n"
        f"🛠️ Evaluation Criteria:\n"
        f"1️⃣ Keyword Optimization (30%)\n"
        f"Extract job-relevant keywords and compare them with the provided job description (if available).\n"
        f"Highlight missing or underused keywords.\n"
        f"Evaluate keyword placement in key sections (Summary, Skills, Experience).\n"
        f"2️⃣ Formatting & ATS Readability (20%)\n"
        f"Check for ATS-friendly formatting (no tables, graphics, columns that could break parsing).\n"
        f"Verify clear section headings ('Work Experience,' 'Education') for accurate parsing.\n"
        f"Ensure proper use of bullet points and font styles for readability.\n"
        f"3️⃣ Section Structuring & Completeness (15%)\n"
        f"Validate the presence of essential sections:\n"
        f"Contact Information (Email, Phone, LinkedIn, Portfolio, etc.)\n"
        f"Summary/Objective Statement\n"
        f"Work Experience (Company, Title, Dates, Responsibilities, Achievements)\n"
        f"Skills Section (Hard & Soft Skills)\n"
        f"Education & Certifications\n"
        f"Additional Sections (Projects, Awards, Volunteer Work, etc.)\n"
        f"Identify any missing sections affecting ATS ranking.\n"
        f"4️⃣ Work Experience & Achievements (15%)\n"
        f"Assess proper job entry structure (Company → Job Title → Dates → Responsibilities).\n"
        f"Check for quantifiable achievements ('Increased revenue by 30%' vs. 'Responsible for sales').\n"
        f"Ensure action-oriented language, avoiding passive descriptions.\n"
        f"5️⃣ Job Match & Customization (10%)\n"
        f"Compare the resume's content against a provided job description.\n"
        f"Generate a Job Match Score (%) based on keyword and experience alignment.\n"
        f"Identify missing qualifications or experience gaps.\n"
        f"6️⃣ Grammar, Consistency & Readability (10%)\n"
        f"Check for grammar, punctuation, and spelling errors.\n"
        f"Assess consistency in formatting, date formats, and tense usage.\n"
        f"Evaluate readability using metrics like Flesch-Kincaid scores.\n\n"
        f"📌 Structured Output Format:\n"
        f"📊 ATS Resume Analysis Report\n"
        f"✅ Final ATS Resume Score: X/100\n"
        f"(A score evaluating ATS compatibility, keyword optimization, formatting, and relevance.)\n\n"
        f"📌 Section-Wise Breakdown:\n"
        f"🔹 Keyword Optimization: X/30\n"
        f"🔹 Formatting & ATS Readability: X/20\n"
        f"🔹 Section Structuring & Completeness: X/15\n"
        f"🔹 Work Experience & Achievements: X/15\n"
        f"🔹 Job Match Score: X/10\n"
        f"🔹 Grammar & Readability: X/10\n\n"
        f"📌 Key Strengths:\n"
        f"✔️ [Highlight 2-3 strong points of the resume]\n\n"
        f"📌 Critical Improvements Needed:\n"
        f"⚠️ [List major issues affecting ATS ranking]\n\n"
        f"📌 Suggested Revisions:\n"
        f"📌 Formatting Fixes: [Specific recommendations]\n"
        f"📌 Keyword Enhancements: [Suggested missing keywords]\n"
        f"📌 Experience Optimization: [How to improve bullet points]\n"
        f"📌 Grammar & Readability: [Key grammar/spelling fixes]\n\n"
        f"📌 Job Match Score (if JD is provided):\n"
        f"📊 X% match with job description.\n"
        f"🔎 Missing Skills/Keywords: [List missing job-relevant terms]\n\n"
        f"🚀 Final Recommendation:\n"
        f"✅ Good to Go | 🟡 Needs Minor Fixes | 🔴 Requires Major Improvement\n\n"
        f"Resume:\n{ats_resume}\n\n"
    )
    response = model.generate_content(prompt)
    return response.text

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

def summarize_resume(resume_text):
    prompt = (
        f"**Objective:** Generate a concise and structured summary of the candidate's resume, focusing on key aspects relevant to a job application.\n\n"
        f"**Instructions:**\n"
        f"1. **Professional Summary:** Provide a high-level overview of the candidate's background, including total years of experience and industry expertise.\n"
        f"2. **Key Skills & Technologies:** List the technical and soft skills mentioned in the resume.\n"
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

def load_pdf_text(file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.read())
        loader = PyPDFLoader(tmp_file.name)
        return ''.join([p.page_content for p in loader.load_and_split()])

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=800,
    chunk_overlap=200,
    length_function=len,
)

def generate_linkedin_search_url(resume_summary):
    prompt = (
        f"**Step 1: Extract Keywords from the Resume**\n"
        f"Please scan the uploaded resume summary and return a JSON decodable string, (properties and values should be in double quotes) with the following structure:\n"
        f"{{\n"
        f"  'roles': ['Role 1', 'Role 2'],\n"  
        f"  'skills': ['Skill 1', 'Skill 2'],\n"
        f"  'technologies': ['Tech 1', 'Tech 2'],\n"
        f"  'locations': ['Location 1', 'Location 2']\n"
        f"}}\n\n"
        f"**Instructions: exclude any soft skills from the skills list**\n"
        f"Extract from this resume summary:\n{resume_summary}\n"
    )
    response = model.generate_content(prompt)
    response_text = response.text

    processing_prompt = (
        f"Given this JSON response from a resume analysis:\n{response_text}\n\n"
        f"Please create a LinkedIn job search URL with the following steps:\n"
        f"1. Parse the JSON and extract the roles, skills, technologies and locations\n"
        f"2. For locations, combine any found locations with: Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Surat, Noida\n"
        f"3. Build search query by combining:\n"
        f"   - Roles with OR between them in quotes\n"
        f"   - Skills with OR between them in quotes\n"
        f"   - Technologies with OR between them in quotes\n"
        f"   - Locations with OR between them in quotes\n"
        f"4. Combine all parts with AND between them\n"
        f"5. Add (\"fulltime\" OR \"internship\") to the query\n"
        f"6. URL encode the query\n"
        f"7. Return the full LinkedIn jobs search URL in this format:\n"
        f"https://www.linkedin.com/jobs/search/?keywords=<encoded_query>\n"
        f"8. Return the URL only, no other text or comments.\n"
    )
    url_response = model.generate_content(processing_prompt)
    linkedin_url = url_response.text.strip()

    return linkedin_url

def generate_cover_letter(resume_summary, job_description, additional_instructions):
    prompt = (
        f"**Objective:** Generate a professional and tailored cover letter for a job application based on the candidate's resume and the job description.\n\n"
        f"**Instructions:**\n"
        f"1. **Cover Letter Structure:**\n"
        f"   - Start with a strong introduction that grabs the attention of the hiring manager.\n"
        f"   - Tailor the letter to the specific job and company.\n"
        f"   - Include relevant skills and experiences that match the job description.\n"
        f"   - Keep the letter concise and to the point.\n"
        f"2. **Resume Summary:**\n"
        f"   - Use the candidate's resume summary to tailor the cover letter.\n"
        f"3. **Job Description:**\n"
        f"   - Use the job description to tailor the cover letter.\n"
        f"4. **Output Format:**\n"
        f"   - Use a professional and formal tone.\n"
        f"   - Keep the letter concise and to the point.\n"
        f"**Data Blocks:**\n"
        f"**Candidate Resume Summary:**\n{resume_summary}\n\n"
        f"**Job Description:**\n{job_description}\n\n"
        f"**Additional Instructions:**\n{additional_instructions}\n\n"
    )
    response = model.generate_content(prompt)
    return response.text


# UI Code
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
        