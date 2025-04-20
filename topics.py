from question_generator import generate_question_bank
import time
import json

def create_question_banks(syllabus):
    """
    Generate and aggregate question banks for each topic and subtopic sequentially.
    Instead of returning a separate JSON for each subtopic, this function appends
    all questions into one aggregated JSON object.
    
    Parameters:
        syllabus (list of dict): Each dict contains a "topic" and a list of "subtopics".
        
    Returns:
        dict: Aggregated JSON with all generated questions under the "questions" key.
    """
    # Debug print to check the received syllabus
    print("Received syllabus:")
    print(syllabus)
    
    # Aggregate all questions into this list
    aggregated_questions = []

    # Process each (topic, subtopic) pair one by one
    for topic_dict in syllabus:
        topic = topic_dict['topic']
        for subtopic in topic_dict['subtopics']:
            print(f"Generating questions for {topic} -> {subtopic}...")
            # Call the question generator (for example with 2 questions per part)
            result = generate_question_bank(topic, subtopic, 2)
            # Expecting result in the form of {"questions": [ ... ]}
            questions = result.get("questions", [])
            print(f"Generated {len(questions)} questions for {subtopic}")
            # Append current questions to aggregated list
            aggregated_questions.extend(questions)
            
            # Optional delay to preserve LLM context and avoid rate limits
            time.sleep(5)
    
    aggregated_data = {"questions": aggregated_questions}
    
    return aggregated_data