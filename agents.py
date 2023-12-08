import requests
import json
import openai
import os
import helper
import random

api_key = "api_key"
with open("../api_key.txt", 'r', encoding='utf-8') as file:
    api_key = file.read()
    
client = openai.OpenAI(api_key = api_key)

def get_request(messages):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    response_format={ "type": "json_object" },
    messages= messages
    )
    return response.choices[0].message.content


def parse_suggested_categories_json(text):
    try:
        json_obj = json.loads(text)
        suggested_categories = json_obj["suggested_categories"]
        if (len(suggested_categories) <= 3):
            return None
        for category in suggested_categories:
            if not isinstance(category, str):
                return None
        return suggested_categories
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {text}: {e}")
    except Exception as e:
        print(f"Error reading file {text}: {e}")
    return None

def fill_suggested_categories(amount, probs_sols, prob_sol_paths, prob_or_sol):
    if amount <= 0:
        return
    ids = random.sample(range(len(probs_sols)), min(len(probs_sols), len(prob_sol_paths), amount))

    for id in ids:
        probs_sol = probs_sols[id]
        if ("suggested_categories" in probs_sol):
            continue
        messages = None
        if prob_or_sol == "problem":
            messages =[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": "Suggest 20 categories for the following programming task. "
                "Give categories which describe this programming task the best. Think about how this programming task might differ from other programming tasks."
                "Give the answer in a JSON format containing a field suggested_categories, which is an array with 20 strings."
                f"These strings are your suggestions. Give the JSON only, nothing else, no other text. Here is the programming task: {probs_sol['desc']}"}
            ]
        else:
            messages =[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": "Suggest 20 categories for the following program. "
                "Give categories which describe this program the best. Think about how this program might differ from other programs."
                "Think about code quality, quantity, any metrics which describe this code."
                "Give the answer in a JSON format containing a field suggested_categories, which is an array with 20 strings."
                f"These strings are your suggestions. Give the JSON only, nothing else, no other text. Here is the program: {probs_sol['source']}"}
            ]
        response = get_request(messages)
        suggested_categories = parse_suggested_categories_json(response)
        if suggested_categories is not None:
            suggested_categories = [element.lower() for element in suggested_categories]
            print("suggested_categories: " + str(suggested_categories))
            file_path = prob_sol_paths[id]
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                data['suggested_categories'] = suggested_categories
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4)

            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {file_path}")
            except Exception as e:
                print(f"An error occurred: {e}")

def count_filed_suggested_categories(probs_sols):
    return len([probs_sol for probs_sol in probs_sols if 'suggested_categories' in probs_sol])


def main():
    problems = helper.problem_getter()
    problem_paths = helper.problem_path_iterator(lambda _, full_path, _3: full_path)

    problem_suggested_categories_count = count_filed_suggested_categories(problems)
    print(f"Already created suggested categories for problems: {problem_suggested_categories_count}")

    fill_suggested_categories(500 - problem_suggested_categories_count, problems, problem_paths, "problem")

    solutions = helper.solution_getter()
    solution_paths = helper.solution_path_iterator(lambda _, full_path, _3: full_path)

    solution_suggested_categories_count = count_filed_suggested_categories(solutions)
    print(f"Already created suggested categories for solutions: {solution_suggested_categories_count}")

    fill_suggested_categories(250 - solution_suggested_categories_count, solutions, solution_paths, "solution")

if __name__ == "__main__":
    main()