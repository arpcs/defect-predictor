import requests
import json
import openai
import os

api_key = "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"
client = openai.OpenAI(api_key = api_key)

def get_request():
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
        {"role": "user", "content": "List 10 smart animals"}
    ]
    )
    print(response.choices[0].message.content)



def parse_and_print_json(file_path):
    num_of_chars = 0
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            json_data = json.loads(content)
            num_of_chars += len(content)
            #print(json_data)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return num_of_chars

def traverse_and_parse(directory):
    num_of_chars_sum = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == "problem.txt":
                file_path = os.path.join(root, file)
                num_of_chars_sum += parse_and_print_json(file_path)
    return num_of_chars_sum

# Replace this with the path to your 'codeforces_problems/10x10' directory
directory_path = "../codeforces_problems/10x10"
num_of_chars_sum = traverse_and_parse(directory_path)

print(num_of_chars_sum)