from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
import json
import requests

# Load environment variables
load_dotenv()

def generate_question_bank(topic, subtopic, question_count):
    """
    Generate a question bank in JSON format for a specific topic and subtopic.
    Instead of writing to a file, the generated questions (augmented with Bloom's Taxonomy)
    are returned as a JSON object.
    
    Parameters:
        topic (str): The main subject area (e.g., "Big Data")
        subtopic (str): Specific area within the topic (e.g., "Introduction to Big Data")
        question_count (int): Number of questions to generate for each part
        
    Returns:
        dict: A JSON object with a key "questions", holding a list of generated questions.
    """
    # Initialize the LLM
    llm = init_chat_model("google/gemma-2-27b-it", model_provider="together")
    
    # Define the messages template
    messages = [
        (
            "system", 
            "You are a highly experienced {topic} college professor and Examination Controller with over 10 years of expertise in designing well-structured and insightful questions on {topic}. "
            "Your role is to craft questions that assess various levels of understanding, ensuring clarity, relevance, and alignment with academic standards. "
            "Provide your response strictly as a JSON array, with each object including the keys: "
            "`Part`, `Question`, `Estimated_Marks`, `Subtopic`, `Topic`, and `Difficulty`. "
            "`Difficulty` should be one of: Easy, Medium, or Hard."
        ),
        (
            "human", 
            "Generate {question_count} questions for each of these three parts (PART A, PART B, PART C) on the topic '{topic}', focusing on the subtopic '{subtopic}':\n\n"
            "- Part A: Short-answer questions\n"
            "- Part B: Medium-length questions\n"
            "- Part C: Long-form questions\n\n"
            "Return the output strictly as a JSON array—no extra formatting."
        )
    ]
    
    # Create the prompt template and invoke it
    prompt_template = ChatPromptTemplate.from_messages(messages)
    prompt = prompt_template.invoke({
        "topic": topic,
        "subtopic": subtopic,
        "question_count": question_count
    })
    
    # Get the result from the LLM
    result = llm.invoke(prompt)
    print("LLM result content:", result.content)
    
    # Parse the new questions from the result (expected to be a JSON array)
    try:
        new_questions = json.loads(result.content)
        if not isinstance(new_questions, list):
            new_questions = [new_questions]
    except Exception as e:
        print("Error parsing new questions:", e)
        new_questions = []
    
    # For each new question, send a POST request to the /predict endpoint with its text
    # and add the returned Bloom's Taxonomy classification
    for question in new_questions:
        question_text = question.get("Question", "")
        payload = {"text": question_text}
        try:
            response = requests.post("https://grand-mackerel-urgently.ngrok-free.app/predict", json=payload)
            if response.status_code == 200:
                bloom_level = response.json().get("bloom_level", "Unknown")
                print(f"Predicted Bloom's level for question: {bloom_level}")
            else:
                print(f"Non-200 response for question: {question_text}")
                bloom_level = "Unknown"
        except Exception as e:
            print(f"Error predicting Bloom's level for question: {question_text}\n{e}")
            bloom_level = "Unknown"
        question["Bloom_Taxonomy"] = bloom_level

    # Aggregate questions into a JSON object (no file usage)
    questions_data = {"questions": new_questions}
    print("Generated questions data:", questions_data)


    # Return the generated JSON object directly
    return questions_data