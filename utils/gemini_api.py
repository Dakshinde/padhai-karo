import json
import urllib.parse
import google.generativeai as genai
import streamlit as st
import os
import io
import re
import json
import PyPDF2
from docx import Document
from google.cloud import vision
import google.generativeai as genai

@st.cache_data
def extract_topics_from_syllabus(syllabus_text):
    """
    Extracts a list of quiz topics from a given syllabus text using the Gemini API.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("GEMINI_API_KEY secret not found!")
            return None
        
        genai.configure(api_key=api_key)
        
        prompt = f"""
        You are an academic assistant. Analyze the following syllabus text and extract a list of main, quiz-worthy topics.
        Focus on specific, concrete subjects. For example, if you see "Unit 3: Trees and Graphs", you should extract "Trees" and "Graphs".

        Syllabus Text:
        ---
        {syllabus_text}
        ---

        **Rules for Generation:**
        1. The output MUST be a single, valid JSON object.
        2. The JSON object must have one key: "topics".
        3. The value of "topics" should be a list of strings.

        Extract the topics now.
        """

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_response)
        
        if "topics" in data and isinstance(data["topics"], list):
            return data["topics"]
        else:
            st.error("Could not parse topics from the syllabus.")
            return None

    except Exception as e:
        st.error(f"An error occurred while analyzing the syllabus: {e}")
        return None

def generate_quiz_from_topic(topic, num_questions, quiz_context):
    """
    Generates a tailored quiz from a given topic, number of questions, and context.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("GEMINI_API_KEY secret not found!")
            return None
        
        genai.configure(api_key=api_key)
        
        prompt = f"""
        You are an expert quiz creator for engineering students. Your task is to create a professional, multiple-choice quiz on the topic of "{topic}".
        The quiz should contain exactly {num_questions} questions.
        The questions should be tailored for a student who is preparing for a "{quiz_context}".
        
        **Rules for Generation:**
        1. The output MUST be a single, valid JSON array `[]`.
        2. Each object must contain these exact keys: "question_text", "options", "correct_answer", "explanation".
        3. The "correct_answer" value MUST be an exact, verbatim copy of one of the strings from the "options" array.
        4. The position of the correct answer in the "options" array MUST be randomized.

        Generate the quiz now.
        """

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        quiz_data = json.loads(cleaned_response)
        
        if isinstance(quiz_data, list) and len(quiz_data) == num_questions:
            return quiz_data
        else:
            st.error("The generated quiz does not have the expected format or number of questions.")
            return None

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def generate_quiz_from_context(context_text, num_questions):
    """
    Generates a quiz based on the provided text content.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("GEMINI_API_KEY secret not found!")
            return None
        
        genai.configure(api_key=api_key)
        
        prompt = f"""
        You are an expert quiz creator. Based ONLY on the following text context, create a multiple-choice quiz with exactly {num_questions} questions.
        The questions must be answerable using only the information in the provided text.

        CONTEXT:
        ---
        {context_text}
        ---

        **Rules for Generation:**
        1. The output MUST be a single, valid JSON array `[]`.
        2. Each object must contain "question_text", "options", "correct_answer", and "explanation".
        3. The "correct_answer" MUST be an exact copy of one of the "options".
        4. The position of the correct answer in the "options" array MUST be randomized.

        Generate the quiz now.
        """

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        quiz_data = json.loads(cleaned_response)
        
        if isinstance(quiz_data, list) and len(quiz_data) == num_questions:
            return quiz_data
        else:
            st.error("The generated quiz does not have the expected format or number of questions.")
            return None

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

@st.cache_data
def get_study_resources(topic, incorrect_questions_tuple):
    """
    Generates study resources with strategies and reliable Google search links.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return None
        genai.configure(api_key=api_key)
        incorrect_questions = [dict(q) for q in incorrect_questions_tuple]
        mistakes_str = "\n".join([f"- {q['question_text']} (Correct Answer: {q['correct_answer']})" for q in incorrect_questions])
        prompt = f"""
        You are a helpful academic tutor. A student struggled with the topic of "{topic}" and made mistakes on these questions:
        {mistakes_str}
        Based on these mistakes, identify 2-3 specific sub-topics they are weak in. For each sub-topic, provide a short study strategy and a concise Google search query.
        **Rules for Generation:**
        1. The output MUST be a JSON object with one key: "study_plan".
        2. The value of "study_plan" should be a list of objects.
        3. Each object must contain three keys: "sub_topic", "study_strategy", and "google_search_query".
        Generate the study plan now.
        """
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        plan_data = json.loads(cleaned_response)
        if "study_plan" in plan_data:
            for item in plan_data["study_plan"]:
                query = urllib.parse.quote_plus(item["google_search_query"])
                item["google_search_link"] = f"https://www.google.com/search?q={query}"
        return plan_data
    except Exception as e:
        print(f"Could not generate study resources: {e}")
        return None

@st.cache_data
def generate_learning_path(topic, incorrect_questions_tuple):
    """
    Generates a personalized, step-by-step learning path.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return None
        genai.configure(api_key=api_key)
        incorrect_questions = [dict(q) for q in incorrect_questions_tuple]
        mistakes_str = "\n".join([f"- {q['question_text']} (Correct Answer: {q['correct_answer']})" for q in incorrect_questions])
        prompt = f"""
        You are an expert academic coach. A student is studying "{topic}" and struggled with concepts revealed by these incorrect quiz answers:
        {mistakes_str}
        Create a personalized 3-step learning path to help them master the topic.
        **Rules for Generation:**
        1. The output MUST be a valid JSON object with one key: "learning_path".
        2. The value of "learning_path" should be a list of 3 step objects.
        3. Each step object must contain three keys: "step_title", "step_details", and "step_rationale".
        Generate the learning path now.
        """
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        path_data = json.loads(cleaned_response)
        return path_data
    except Exception as e:
        print(f"Could not generate learning path: {e}")
        return None
    

# ---------------------- OCR for Images ----------------------
def ocr_image_bytes(image_bytes):
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.document_text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)
        return response.full_text_annotation.text or ""
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

# ---------------------- Syllabus Processing ----------------------
def process_syllabus(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name.lower()
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            return ocr_image_bytes(file_bytes)
        elif filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for p in reader.pages:
                text += (p.extract_text() or "") + "\n"
            return text
        else:
            return ""
    except Exception as e:
        print(f"process_syllabus error: {e}")
        return ""

# ---------------------- PYQ Processing ----------------------
def extract_text_from_pdf_bytes(file_bytes):
    text = ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
    except Exception as e:
        print(f"extract_text_from_pdf_bytes error: {e}")
    return text

def extract_text_from_docx_bytes(file_bytes):
    text = ""
    try:
        doc = Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"extract_text_from_docx_bytes error: {e}")
    return text

def process_pyqs(pyq_files):
    combined = ""
    for f in pyq_files:
        try:
            fb = f.getvalue()
            name = f.name.lower()
            combined += f"\n\n--- FILE: {f.name} ---\n"
            if name.endswith('.pdf'):
                combined += extract_text_from_pdf_bytes(fb)
            elif name.endswith('.docx'):
                combined += extract_text_from_docx_bytes(fb)
        except Exception as e:
            print(f"process_pyqs error: {e}")
    return combined

# ---------------------- AI Generator ----------------------
def _clean_json_like(text):
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text

def generate_module_question_bank(syllabus_text, pyqs_text, course_objectives=None):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            from streamlit import secrets
            api_key = secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)

        def trim(s, n=20000):
            return s if len(s) <= n else s[:n] + " [TRUNCATED]"

        prompt = f"""
You are an expert academic analyzer. 
From the syllabus and PYQs provided, generate a MODULE-WISE PYQ Question Bank.

--- SYLLABUS ---
{trim(syllabus_text, 16000)}
--- PYQS ---
{trim(pyqs_text, 32000)}
--- COURSE OBJECTIVES ---
{course_objectives or '[none]'}
-------------------------------

Instructions:
1. Identify clear module names from the syllabus.
2. Extract individual questions from the PYQs.
3. Group questions by relevant module.
4. Count how often each unique question/concept repeats (repetition_count).
5. Mark "importance": "High" if repetition_count > 1 (or if strongly tied to objectives), else "Normal".
6. Output ONLY a valid JSON object, like this:
{{
  "Module 1": [
    {{
      "question_text": "Explain bubble sort.",
      "repetition_count": 3,
      "importance": "High"
    }}
  ],
  "Module 2": [...]
}}

Generate now:
"""

        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        raw = response.text.strip()
        json_str = _clean_json_like(raw)
        data = json.loads(json_str)

        # Normalize
        output = {}
        for module, qs in data.items():
            clean_list = []
            for q in qs:
                qt = q.get("question_text", "").strip()
                rep = int(q.get("repetition_count", 0))
                imp = q.get("importance", "Normal")
                clean_list.append({
                    "question_text": qt,
                    "repetition_count": rep,
                    "importance": imp
                })
            output[module] = clean_list
        return output
    except Exception as e:
        print(f"generate_module_question_bank error: {e}")
        return None

# ---------------------- MODULE-WISE PYQ PDF EXPORT ----------------------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas as pdfcanvas
import io
from datetime import datetime

class NumberedCanvas(pdfcanvas.Canvas):
    """Custom canvas to add page numbers and footer text."""
    def __init__(self, *args, footer_text: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.footer_text = footer_text

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        page_num_text = f"Page {self._pageNumber} of {page_count}"
        width, height = A4
        self.setFont("Helvetica", 9)
        self.drawCentredString(width / 2.0, 15, page_num_text)
        if self.footer_text:
            self.drawString(36, 15, self.footer_text)

def export_question_bank_pdf(subject_name, question_bank):
    """
    Export module-wise PYQ question bank as a PDF.
    Uses ⭐ for high-importance questions and bullets for normal ones.
    Continuous layout; no empty pages between modules.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=36, leftMargin=36,
                            topMargin=72, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name="TitleCentered", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=12)
    module_style = styles["Heading3"]
    body_style = styles["BodyText"]
    footer_text = "Generated and created by Padhai Karo"

    story = []

    # Cover page
    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph("Module-wise Question Bank", title_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Subject: <b>{subject_name}</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))
    date_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Generated on: {date_str}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(footer_text, styles["Normal"]))
    story.append(PageBreak())

    # Modules content
    for module_name, questions in question_bank.items():
        story.append(Paragraph(module_name, module_style))
        story.append(Spacer(1, 0.08 * inch))
        # sort: high importance first
        qs_sorted = sorted(questions, key=lambda q: (0 if q.get("importance", "").lower() == "high" else 1,
                                                     -int(q.get("repetition_count", 0))))
        for q in qs_sorted:
            qt = q.get("question_text", "").strip()
            rep = q.get("repetition_count", 0)
            imp = q.get("importance", "Normal")
            if imp.lower() == "high":
                para_text = f"<b>⭐ {qt}</b> — (repeated {rep} times)"
            else:
                para_text = f"• {qt} — (repeated {rep} times)"
            story.append(Paragraph(para_text, body_style))
            story.append(Spacer(1, 0.06 * inch))
        story.append(Spacer(1, 0.12 * inch))

    # Final footer
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(footer_text, styles["Normal"]))

    doc.build(story, canvasmaker=lambda *args, **kwargs: NumberedCanvas(*args, footer_text=footer_text, **kwargs))
    buffer.seek(0)
    return buffer
