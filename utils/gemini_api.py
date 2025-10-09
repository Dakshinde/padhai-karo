import json
import google.generativeai as genai
import streamlit as st

@st.cache_data
def get_study_resources(topic, incorrect_questions_tuple):
    # This function is not part of the current problem, so we leave it as is.
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: return None
        genai.configure(api_key=api_key)
        incorrect_questions = [dict(q) for q in incorrect_questions_tuple]
        mistakes_str = "\n".join([f"- {q['question_text']} (Correct Answer: {q['correct_answer']})" for q in incorrect_questions])
        prompt = f"""
        You are a helpful academic tutor. A student is struggling with the topic of "{topic}" and made mistakes on the following questions:
        {mistakes_str}
        Based on these specific mistakes, recommend 3 to 4 targeted sub-topics to study. For each sub-topic, provide one high-quality, relevant online resource link.
        **Rules for Generation:**
        1. The output MUST be a single, valid JSON object with one key: "study_resources".
        2. The value should be a list of objects, each containing "sub_topic" and "resource_link".
        Generate the study resources now.
        """
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        resources = json.loads(cleaned_response)
        return resources
    except Exception as e:
        print(f"Could not generate study resources: {e}")
        return None

def generate_quiz_from_topic(topic, num_questions, quiz_context):
    """
    Generates a tailored quiz with debug print statements.
    """
    print("--- DEBUG: Starting generate_quiz_from_topic function ---")
    try:
        print("DEBUG: Checkpoint 1 - Getting API key...")
        api_key = st.secrets.get("GEMINI_API_KEY")
        
        if not api_key:
            print("DEBUG: API key not found!")
            st.error("GEMINI_API_KEY secret not found!")
            return None
        
        print("DEBUG: Checkpoint 2 - API key found. Configuring genai...")
        genai.configure(api_key=api_key)
        
        prompt = f"""
        You are an expert quiz creator for engineering students. Your task is to create a multiple-choice quiz on the topic of "{topic}".
        The quiz should contain exactly {num_questions} questions tailored for a student preparing for a "{quiz_context}".
        **Rules for Generation:**
        1. The output MUST be a single, valid JSON array `[]`.
        2. Each object must contain these exact keys: "question_text", "options", "correct_answer", "explanation".
        Generate the quiz now.
        """

        print("DEBUG: Checkpoint 3 - Creating the model...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        print("DEBUG: Checkpoint 4 - Calling the API to generate content...")
        response = model.generate_content(prompt)
        
        print("DEBUG: Checkpoint 5 - Content received. Cleaning and parsing JSON...")
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        quiz_data = json.loads(cleaned_response)
        
        if isinstance(quiz_data, list) and len(quiz_data) == num_questions:
            print("--- DEBUG: Function finished successfully ---")
            return quiz_data
        else:
            st.error("The generated quiz does not have the expected format or number of questions.")
            return None

    except Exception as e:
        print(f"--- DEBUG: An error occurred in the function: {e} ---")
        st.error(f"An unexpected error occurred: {e}")
        return None