# 🎯 AI-Powered Job Fit Assessment

## Description

This AI-Powered Job Fit Assessment tool helps streamline the job application process by analyzing the alignment between resumes and job requirements. The system provides comprehensive evaluations of candidates' fit for positions, making it easier for both recruiters and job seekers to assess compatibility.

The tool uses advanced natural language processing to:

- Analyze resumes against job requirements
- Provide detailed alignment analysis
- Calculate fit percentages
- Offer improvement suggestions
- Generate comprehensive recommendations

## Preview

<img src="./assets/preveiw1.png" width="100%" />
<br>
<img src="./assets/preveiw2.png" width="100%" />
<br>
<img src="./assets/preveiw3.png" width="100%" />
<br>
<img src="./assets/preveiw4.png" width="100%" />

## Technologies Used

- Python
- Streamlit
- LangChain
- Google Gemini AI
- PyPDF2
- TOML Configuration

## Features

- PDF resume upload
- PDF/TXT job requirements upload
- Custom theme configuration
- Detailed alignment analysis
- Percentage-based fit scoring
- Actionable improvement suggestions
- Additional context input option

## Setup and Configuration

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key

### Environment Setup

1. Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/job-fit-assessment.git
```

2. Navigate to the project directory:

```bash
cd job-fit-assessment
```

3. Create a virtual environment:

```bash
python -m venv venv
```

4. Activate the virtual environment:

```bash
source venv/bin/activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Run the application:

```bash
streamlit run app.py
```

## Usage

1. Upload your resume (PDF format)
2. Upload job requirements (PDF or TXT format)
3. (Optional) Add any specific instructions or context
4. Click "Analyze" to get a detailed assessment
5. Review the fit percentage and detailed analysis
6. Use the suggestions to improve your application
