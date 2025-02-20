import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import tempfile

# Load and configure Gemini
dotenv_path = ".env"
load_dotenv(dotenv_path)
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError(f"Unable to retrieve GEMINI_API_KEY from {dotenv_path}")

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

def summarize_text(text):
    prompt = f"Please summarize the following text concisely:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

def ats_score(ats_resume):
    # Define the prompt with detailed ATS evaluation criteria
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

    #     f"""
    # Analyze the uploaded resume with an in-depth **Applicant Tracking System (ATS) evaluation**. 
    # Provide a **detailed ATS compatibility score** based on **keyword optimization, formatting, readability, structuring, and job relevance**. 
    # Identify strengths, weaknesses, and actionable improvements for better ATS performance.

    # ---
    # ## 📌 **ATS Resume Analysis Report**

    # ### 🟢 **Final ATS Resume Score: _X/100_**  
    # (A detailed evaluation of ATS compatibility, keyword optimization, formatting, and relevance.)

    # ---
    # ### 📊 **Section-Wise Breakdown**  

    # | **Criteria**                           | **Score** | **Remarks** |  
    # |-----------------------------------------|----------|-------------|  
    # | ✅ **Keyword Optimization** (30%)       | _X/30_   | [Brief remark] |  
    # | ✅ **Formatting & ATS Readability** (20%) | _X/20_   | [Brief remark] |  
    # | ✅ **Section Structuring & Completeness** (15%) | _X/15_   | [Brief remark] |  
    # | ✅ **Work Experience & Achievements** (15%) | _X/15_   | [Brief remark] |  
    # | ✅ **Job Match Score** (10%) | _X/10_   | [Brief remark] |  
    # | ✅ **Grammar & Readability** (10%) | _X/10_   | [Brief remark] |  
    # | **🟠 Total Score** | **_X/100_** | **Overall ATS Compatibility** |  

    # ---
    # ### 🟢 **Key Strengths**  
    # ✔️ **[Point 1]**  
    # ✔️ **[Point 2]**  
    # ✔️ **[Point 3]**  

    # ---
    # ### 🔴 **Critical Issues & Recommended Fixes**  

    # #### 1️⃣ **Formatting & ATS Readability Issues:**  
    # 🚫 **[Issue 1]** → ✅ **[Suggested Fix]**  
    # 🚫 **[Issue 2]** → ✅ **[Suggested Fix]**  

    # #### 2️⃣ **Missing Keywords & Job Relevance:**  
    # 🔎 **Missing Keywords:** [List missing job-specific terms]  
    # 📌 **Suggested Additions:** [Recommended keyword insertions]  

    # #### 3️⃣ **Work Experience & Achievements:**  
    # ❌ **[Weak bullet point]** → ✅ **[Rewritten strong bullet point]**  

    # #### 4️⃣ **Grammar & Readability Issues:**  
    # 📝 **[Grammar mistake]** → ✅ **[Suggested correction]**  

    # ---
    # ### 📌 **Job Match Score (if JD is provided)**  
    # 📊 **_X% match_** with job description  
    # 🔎 **Missing Required Skills/Experience:**  
    # - [Skill 1]  
    # - [Skill 2]  
    # - [Skill 3]  

    # ---
    # ### 🚀 **Final Recommendation:**  
    # 🟢 **Good to Go** (90-100)  
    # 🟡 **Needs Minor Fixes** (70-89)  
    # 🔴 **Requires Major Improvement** (Below 70)  

    # ---
    # Ensure the feedback is **clear, actionable, and structured** for better ATS performance. 
    # Return the final result in the given structured format.

    # Resume:
    # {ats_resume}

    # """
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

# Initialize text splitter
text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=800,
    chunk_overlap=200,
    length_function=len,
) 