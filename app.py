import streamlit as st
from utils.gemini_api import generate_quiz_from_topic, get_study_resources, generate_learning_path

st.set_page_config(
    page_title="Padhai Karo - Personalized Engineering Tutor",
    layout="centered"
)

st.title("Padhai Karo - Your Personalized Engineering Tutor")

# Initialize session state variables
for key in ['quiz_data', 'user_answers', 'topic_input']:
    if key not in st.session_state:
        st.session_state[key] = None

# --- UI for Quiz Configuration ---
if st.session_state.quiz_data is None:
    with st.form("quiz_config_form"):
        st.header("1. Configure Your Quiz")
        st.session_state.topic_input = st.text_input("What topic do you want a quiz on?", placeholder="e.g., 'Red-Black Trees'")
        # --- SLIDER REVERTED HERE ---
        num_questions = st.slider("Number of Questions:", min_value=5, max_value=20, value=5)
        quiz_context = st.selectbox(
            "Why are you taking this quiz?",
            ("Quick Review", "Semester Exam Preparation", "Viva / Oral Exam Practice")
        )
        
        submitted_config = st.form_submit_button("Generate Quiz!")
        if submitted_config:
            if st.session_state.topic_input:
                with st.spinner("Generating your quiz... This might take a moment!"):
                    st.session_state.quiz_data = generate_quiz_from_topic(st.session_state.topic_input, num_questions, quiz_context)
                    st.rerun()
            else:
                st.warning("Please enter a topic to generate a quiz.")

# --- Display the Quiz Form ---
if st.session_state.quiz_data and st.session_state.user_answers is None:
    st.header("2. Take the Quiz")
    with st.form("quiz_form"):
        temp_user_answers = {}
        for i, q in enumerate(st.session_state.quiz_data):
            st.subheader(f"Question {i+1}: {q['question_text']}")
            temp_user_answers[i] = st.radio("Choose one:", q['options'], key=f"q{i}")

        submitted_answers = st.form_submit_button("Submit Answers")
        if submitted_answers:
            st.session_state.user_answers = temp_user_answers
            st.rerun()

# --- Display the Results and Study Plan ---
if st.session_state.user_answers:
    st.header("3. Your Results")

    quiz_data = st.session_state.quiz_data
    user_answers = st.session_state.user_answers
    
    score = 0
    incorrect_questions = []
    for i, q in enumerate(quiz_data):
        if user_answers[i].strip() == q['correct_answer'].strip():
            score += 1
        else:
            incorrect_questions.append(q)
    
    score_percent = score / len(quiz_data)
    score_message = f"You scored {score} out of {len(quiz_data)}!"

    if score_percent >= 0.9:
        st.success(score_message)
    elif score_percent >= 0.5:
        st.warning(score_message)
    else:
        st.error(score_message)
    
    st.divider()

    st.subheader("Detailed Feedback")
    for i, q in enumerate(quiz_data):
        with st.expander(f"Question {i+1}: Review", expanded=(user_answers[i].strip() != q['correct_answer'].strip())):
            st.markdown(f"**Question:** {q['question_text']}")
            user_ans = user_answers[i]
            correct_ans = q['correct_answer']
            
            if user_ans.strip() == correct_ans.strip():
                st.markdown(f"**Your answer:** {user_ans} (Correct)")
            else:
                st.markdown(f"**Your answer:** {user_ans} (Incorrect)")
                st.markdown(f"**Correct answer:** {correct_ans}")
            st.info(f"**Explanation:** {q['explanation']}")

    # --- Generate and Display Learning Path and Resources ---
    if incorrect_questions:
        st.divider()
        st.subheader("Your Personalized Study Plan")
        
        incorrect_questions_tuple = tuple(tuple(d.items()) for d in incorrect_questions)
        
        with st.spinner("Generating your personalized plan..."):
            learning_path = generate_learning_path(st.session_state.topic_input, incorrect_questions_tuple)
            study_resources = get_study_resources(st.session_state.topic_input, incorrect_questions_tuple)

        # Display Learning Path
        if learning_path and "learning_path" in learning_path:
            st.markdown("Here is a step-by-step path to improve your understanding:")
            for i, step in enumerate(learning_path["learning_path"]):
                with st.container(border=True):
                    st.markdown(f"**Step {i+1}: {step['step_title']}**")
                    st.markdown(f"**Action:** {step['step_details']}")
                    st.caption(f"**Why:** {step['step_rationale']}")
        
        # Display Study Resources
        if study_resources and "study_plan" in study_resources:
            st.divider()
            st.subheader("Recommended Study Resources")
            for item in study_resources["study_plan"]:
                with st.container(border=True):
                    st.markdown(f"**Sub-Topic to Review:** {item['sub_topic']}")
                    st.markdown(f"**How to Study:** {item['study_strategy']}")
                    st.link_button("Search for this topic", item['google_search_link'])

    st.divider()
    if st.button("Take Another Quiz"):
        for key in ['quiz_data', 'user_answers', 'topic_input']:
            st.session_state[key] = None
        st.rerun()