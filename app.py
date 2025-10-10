import streamlit as st
import time
import io
import PyPDF2
from pptx import Presentation
from docx import Document
from utils.gemini_api import (
    generate_quiz_from_topic, 
    get_study_resources, 
    generate_learning_path,
    extract_topics_from_syllabus,
    generate_quiz_from_context
)

# --- Helper Functions for Text Extraction ---
def extract_text_from_pdf(file_bytes):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_pptx(file_bytes):
    presentation = Presentation(io.BytesIO(file_bytes))
    text = ""
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text

def extract_text_from_docx(file_bytes):
    document = Document(io.BytesIO(file_bytes))
    text = ""
    for para in document.paragraphs:
        text += para.text + "\n"
    return text

# --- Page & Session State Configuration ---
st.set_page_config(page_title="Padhai Karo", layout="centered")
st.title("Padhai Karo - Your Personalized Engineering Tutor")

keys_to_init = ['quiz_data', 'user_answers', 'quiz_topic', 'start_time', 'syllabus_topics']
for key in keys_to_init:
    if key not in st.session_state:
        st.session_state[key] = None

# --- Main Application Logic ---

# STATE 1: A quiz is active
if st.session_state.quiz_data and st.session_state.user_answers is None:
    st.header(f"Quiz on: {st.session_state.quiz_topic}")
    with st.form("quiz_form"):
        temp_user_answers = {}
        for i, q in enumerate(st.session_state.quiz_data):
            st.subheader(f"Question {i+1}: {q['question_text']}")
            temp_user_answers[i] = st.radio("Choose one:", q['options'], key=f"q{i}", index=None)
        
        if st.form_submit_button("Submit Answers"):
            st.session_state.user_answers = temp_user_answers
            st.rerun()

# STATE 2: A quiz has been submitted and results are shown
elif st.session_state.user_answers:
    st.header("Your Results")
    quiz_data = st.session_state.quiz_data
    user_answers = st.session_state.user_answers
    
    score = 0
    incorrect_questions = []
    for i, q in enumerate(quiz_data):
        if user_answers.get(i, "").strip() == q['correct_answer'].strip():
            score += 1
        else:
            incorrect_questions.append(q)
    
    score_percent = score / len(quiz_data)
    if score_percent >= 0.9: st.success(f"You scored {score} out of {len(quiz_data)}!")
    elif score_percent >= 0.5: st.warning(f"You scored {score} out of {len(quiz_data)}!")
    else: st.error(f"You scored {score} out of {len(quiz_data)}!")
    
    st.subheader("Detailed Feedback")
    for i, q in enumerate(quiz_data):
        with st.expander(f"Question {i+1}: Review", expanded=(user_answers.get(i, "").strip() != q['correct_answer'].strip())):
            st.markdown(f"**Question:** {q['question_text']}")
            if user_answers.get(i, "").strip() == q['correct_answer'].strip():
                st.success(f"Your answer: {user_answers.get(i)} (Correct)")
            else:
                st.error(f"Your answer: {user_answers.get(i)} (Incorrect)")
                st.success(f"Correct answer: {q['correct_answer']}")
            st.info(f"**Explanation:** {q['explanation']}")
    
    if incorrect_questions:
        incorrect_questions_tuple = tuple(tuple(d.items()) for d in incorrect_questions)
        with st.spinner("Generating your personalized plan..."):
            learning_path = generate_learning_path(st.session_state.quiz_topic, incorrect_questions_tuple)
            study_resources = get_study_resources(st.session_state.quiz_topic, incorrect_questions_tuple)
        
        if learning_path and "learning_path" in learning_path:
            st.divider()
            st.subheader("Your Personalized Learning Path")
            for i, step in enumerate(learning_path["learning_path"]):
                with st.container(border=True):
                    st.markdown(f"**Step {i+1}: {step['step_title']}**")
                    st.markdown(f"**Action:** {step['step_details']}")
                    st.caption(f"**Why:** {step['step_rationale']}")
        
        if study_resources and "study_plan" in study_resources:
            st.divider()
            st.subheader("Recommended Study Resources")
            for item in study_resources["study_plan"]:
                with st.container(border=True):
                    st.markdown(f"**Sub-Topic to Review:** {item['sub_topic']}")
                    st.markdown(f"**How to Study:** {item['study_strategy']}")
                    st.link_button("Search for this topic", item['google_search_link'])

    st.divider()
    if st.button("Start a New Quiz"):
        for key in keys_to_init:
            st.session_state[key] = None
        st.rerun()

# STATE 3: The initial home screen for generating a quiz
else:
    st.header("1. Choose Your Quiz Method")
    
    topic_tab, syllabus_tab, notes_tab = st.tabs(["By Topic", "From Syllabus", "From My Notes"])

    with topic_tab:
        with st.form("topic_quiz_form"):
            st.subheader("Generate a quiz from any topic name")
            topic_input = st.text_input("What topic do you want a quiz on?", placeholder="e.g., 'Red-Black Trees'")
            num_questions_topic = st.slider("Number of Questions:", min_value=5, max_value=20, value=5, key="topic_q")
            quiz_context_topic = st.selectbox("Quiz Purpose:", ("Quick Review / Viva Prep", "Semester Exam Prep"), key="topic_c")
            if st.form_submit_button("Generate Quiz"):
                if topic_input:
                    st.session_state.quiz_topic = topic_input
                    with st.spinner("Generating your quiz..."):
                        st.session_state.quiz_data = generate_quiz_from_topic(topic_input, num_questions_topic, quiz_context_topic)
                        st.rerun()
                else:
                    st.warning("Please enter a topic.")

    with syllabus_tab:
        st.subheader("Analyze a syllabus to generate quiz topics")
        if st.session_state.syllabus_topics is None:
            syllabus_text = st.text_area("Paste your course syllabus here:", height=200)
            if st.button("Analyze Syllabus"):
                if syllabus_text:
                    with st.spinner("Analyzing syllabus..."):
                        st.session_state.syllabus_topics = extract_topics_from_syllabus(syllabus_text)
                        st.rerun()
                else:
                    st.warning("Please paste your syllabus text.")
        else:
            st.info("Syllabus analyzed! Now configure your quiz below.")
            with st.form("syllabus_quiz_form"):
                selected_topic = st.selectbox("Choose a topic from your syllabus:", options=st.session_state.syllabus_topics)
                num_questions_syllabus = st.slider("Number of Questions:", min_value=5, max_value=20, value=5, key="syllabus_q")
                quiz_context_syllabus = st.selectbox("Quiz Purpose:", ("Quick Review", "Semester Exam Prep"), key="syllabus_c")
                if st.form_submit_button("Generate Quiz from Syllabus Topic"):
                    st.session_state.quiz_topic = selected_topic
                    with st.spinner("Generating your quiz..."):
                        st.session_state.quiz_data = generate_quiz_from_topic(selected_topic, num_questions_syllabus, quiz_context_syllabus)
                        st.rerun()

    with notes_tab:
        st.subheader("Upload your notes to generate a quiz")
        with st.form("notes_quiz_form"):
            uploaded_file = st.file_uploader("Upload your notes (PDF, PPTX, DOCX)", type=['pdf', 'pptx', 'docx'])
            num_questions_notes = st.slider("Number of Questions:", min_value=5, max_value=20, value=5, key="notes_q")
            if st.form_submit_button("Generate Quiz from My Notes"):
                if uploaded_file is not None:
                    extracted_text = ""
                    with st.spinner(f"Reading your file: {uploaded_file.name}..."):
                        file_bytes = uploaded_file.getvalue()
                        try:
                            if uploaded_file.type == "application/pdf":
                                extracted_text = extract_text_from_pdf(file_bytes)
                            elif "presentationml" in uploaded_file.type:
                                extracted_text = extract_text_from_pptx(file_bytes)
                            elif "wordprocessingml" in uploaded_file.type:
                                extracted_text = extract_text_from_docx(file_bytes)
                        except Exception as e:
                            st.error(f"Could not read the file. Error: {e}")
                    
                    if extracted_text:
                        st.session_state.quiz_topic = f"your document '{uploaded_file.name}'"
                        with st.spinner("Generating quiz from document..."):
                            st.session_state.quiz_data = generate_quiz_from_context(extracted_text, num_questions_notes)
                            st.rerun()
                    else:
                        st.warning("Could not extract text from the document.")
                else:
                    st.warning("Please upload a file.")