import requests

# Define the syllabus data as a JSON array
syllabus_data = [
    {
        "topic": "Big data",
        "subtopics": [
            "Introduction to Big Data",
            "Data Storage Solutions",
        ]
    }
]

# Send a POST request to the /syllabus endpoint with JSON payload
response = requests.post("http://localhost:8000/syllabus", json=syllabus_data)

# Print the response from the server
print(response.json())

# Uncomment the following lines to download the generated question bank
# response = requests.get("http://localhost:8000/question_bank")
# with open('question_bank.csv', 'wb') as f:
#     f.write(response.content)