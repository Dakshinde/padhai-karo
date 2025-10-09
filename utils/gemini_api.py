import json
import urllib.parse
import google.generativeai as genai
import streamlit as st

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
        3. **CRITICAL:** The "correct_answer" value MUST be an exact, verbatim copy of one of the strings from the "options" array.
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

        # Post-process to add the full URL
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