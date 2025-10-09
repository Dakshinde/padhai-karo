import streamlit as st
from utils.gemini_api import generate_quiz_from_topic, get_study_resources

st.set_page_config(
    page_title="Padhai Karo - Personalized Engineering Tutor",
    layout="centered"
)

st.title("Padhai Karo - Your Personalized Engineering Tutor")

# Initialize session state variables
for key in ['quiz_data', 'user_answers', 'study_resources', 'topic_input']:
    if key not in st.session_state:
        st.session_state[key] = None

# --- UI for Quiz Configuration ---
if st.session_state.quiz_data is None:
    with st.form("quiz_config_form"):
        st.header("1. Configure Your Quiz")
        st.session_state.topic_input = st.text_input("What topic do you want a quiz on?", placeholder="e.g., 'Red-Black Trees'")
        num_questions = st.slider("Number of Questions:", min_value=3, max_value=15, value=5)
        quiz_context = st.selectbox(
            "Why are you taking this quiz?",
            ("Quick Review", "Semester Exam Preparation", "Viva / Oral Exam Practice")
        )
        
        submitted_config = st.form_submit_button("Generate Quiz!")
        if submitted_config:
            if st.session_state.topic_input:
                with st.spinner("Generating your quiz... This might take a moment!"):
                    st.session_state.quiz_data = generate_quiz_from_topic(st.session_state.topic_input, num_questions, quiz_context)
                    st.rerun() # Rerun to hide config and show quiz
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
            st.rerun() # Rerun to show results

# --- Display the Results and Study Resources ---
if st.session_state.user_answers:
    st.header("3. Your Results")

    quiz_data = st.session_state.quiz_data
    user_answers = st.session_state.user_answers
    
    score = 0
    incorrect_questions = []
    for i, q in enumerate(quiz_data):
        if user_answers[i] == q['correct_answer']:
            score += 1
        else:
            incorrect_questions.append(q)
    
    st.success(f"You scored {score} out of {len(quiz_data)}!")
    st.divider()

    st.subheader("Detailed Feedback")
    for i, q in enumerate(quiz_data):
        st.markdown(f"**Question {i+1}: {q['question_text']}**")
        user_ans = user_answers[i]
        correct_ans = q['correct_answer']
        
        if user_ans == correct_ans:
            st.markdown(f"**Your answer:** {user_ans} (Correct)")
        else:
            st.markdown(f"**Your answer:** {user_ans} (Incorrect)")
            st.markdown(f"**Correct answer:** {correct_ans}")
        st.info(f"**Explanation:** {q['explanation']}")
        st.divider()

    if incorrect_questions:
        st.subheader("Recommended Study Resources")
        # To make the list hashable for caching, we convert it to a tuple of tuples
        incorrect_questions_tuple = tuple(tuple(d.items()) for d in incorrect_questions)
        resources = get_study_resources(st.session_state.topic_input, incorrect_questions_tuple)
        
        if resources and "study_resources" in resources:
            for resource in resources["study_resources"]:
                st.markdown(f"- **Topic:** {resource['sub_topic']}")
                st.markdown(f"  **Resource:** [Click here to study]({resource['resource_link']})")
        else:
            st.warning("Could not retrieve study resources at this time.")

    # --- NEW "START OVER" BUTTON ---
    st.divider()
    if st.button("Take Another Quiz"):
        # Reset all relevant session state variables
        for key in ['quiz_data', 'user_answers', 'study_resources', 'topic_input']:
            st.session_state[key] = None
        st.rerun()