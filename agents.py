import requests
import json
import openai
import os
import helper
import random
from typing import List

api_key = "api_key"
with open("../api_key.txt", 'r', encoding='utf-8') as file:
    api_key = file.read()
    
client = openai.OpenAI(api_key = api_key)

def get_request(messages, is_gpt_4 = False):
    if is_gpt_4 == False:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages= messages
        )
        return response.choices[0].message.content
    else:
        response = client.chat.completions.create(
        model="gpt-4-1106-preview",
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

picked_categories = ['mathematics', 'dynamic programming', 'bit manipulation', 'greedy', 'brute force', 'graphs', 
    'sortings', 'search', 'trees', 'strings', 'number theory', 'combinatorics', 'two pointers', 'geometry', 'shortest paths',
    'divide and conquer', 'probabilities', 'data structures', 'game theory', '2d, 3d','Recursive','Well-Commented','Self-Documenting',
    'Complex','readable','Well-Named','Efficient','Reusable','Documented','Good error-Handling', 'Good solution', 'COMPILATION ERROR', 'RUNTIME ERROR']
good_verdicts = ["FAILED", "OK", "PARTIAL", "COMPILATION_ERROR", "RUNTIME_ERROR", "WRONG_ANSWER"]

def filter_pack_solutions(container: helper.ProblemSolutionContainer, packs: List[helper.ProblemPack], pack_solution_size):
    filtered_packs = []
    for pack in packs:
        filtered_solutions = []
        got_already = 0
        for verdict in good_verdicts:
            num_to_get = int(pack_solution_size / 2 if verdict == "OK" else pack_solution_size / 10)
            if verdict == "WRONG_ANSWER":
                num_to_get = pack_solution_size - got_already
            for solution_id in pack.get_solution_ids():
                solution_obj = container.solutions[solution_id]
                if (solution_obj['verdict'] == verdict and num_to_get > 0):
                    filtered_solutions.append(solution_id)
                    num_to_get -= 1
                    got_already += 1
        filtered_packs.append(helper.ProblemPack(pack.get_problem_id(), filtered_solutions))
    return filtered_packs

defect_eval_ver = 'defect_evaluation_v4'
defect_eval_gpt4_ver = 'defect_evaluation_gpt4_v4'

def pick_problem_packs(container: helper.ProblemSolutionContainer, number_of_small_packs=15, small_pack_solution_size=10, number_of_big_packs=5, big_pack_solution_size=30):
    filtered_packs = []
    for index, problem in enumerate(container.problems):
        try:
            solutions = container.get_solutions_for_problem(index)
            if len(solutions) > big_pack_solution_size:
                good_soltion_count = 0
                good_solution_ids = []
                good_soltion_count_by_verdict = {}
                for solution in solutions:
                    solution_obj = container.solutions[solution]
                    if ('C++' in solution_obj['programmingLanguage'] and  solution_obj["testset"] == "TESTS"):
                        good_soltion_count += 1
                        good_soltion_count_by_verdict[solution_obj['verdict']] = good_soltion_count_by_verdict.get(solution_obj['verdict'], 0) + 1
                        good_solution_ids.append(solution)
                if (good_soltion_count >= big_pack_solution_size and 
                good_soltion_count_by_verdict['OK'] >= big_pack_solution_size/2 and 
                good_soltion_count_by_verdict['RUNTIME_ERROR'] >= big_pack_solution_size/10 and
                good_soltion_count_by_verdict['COMPILATION_ERROR'] >= big_pack_solution_size/10 and 
                good_soltion_count_by_verdict['WRONG_ANSWER'] >= big_pack_solution_size/3):
                    filtered_packs.append(helper.ProblemPack(index, good_solution_ids))
        except Exception as e:
            pass

    already_done_packs = []
    for pack in filtered_packs:
        problem_obj = container.problems[pack.problem_id]
        good = False
        for solution_id in pack.get_solution_ids():
            solution_obj = container.solutions[solution_id]
            if defect_eval_ver in solution_obj or defect_eval_gpt4_ver in solution_obj:
                good = True
        if "category_evaluation" in problem_obj or good:
            already_done_packs.append(pack)

    filtered_packs = [obj for obj in filtered_packs if obj not in already_done_packs]
    random_packs =  random.sample(filtered_packs, min(len(filtered_packs), number_of_small_packs + number_of_big_packs))

    small_packs = random_packs[:number_of_small_packs]
    big_packs = random_packs[number_of_small_packs: (number_of_big_packs + number_of_small_packs)]

    already_done_packs = filter_pack_solutions(container, already_done_packs, big_pack_solution_size)
    small_packs = filter_pack_solutions(container, small_packs, small_pack_solution_size)
    big_packs = filter_pack_solutions(container, big_packs, big_pack_solution_size)

    return_new_packs = small_packs + big_packs
    pick_this_many = (number_of_big_packs + number_of_small_packs - len(already_done_packs))
    pick_this_many = pick_this_many if pick_this_many > 0 else 0
    return_new_packs = return_new_packs[:pick_this_many]
    return_packs = already_done_packs + return_new_packs

    final_return = return_packs[:(number_of_big_packs + number_of_small_packs)]
    return final_return

def parse_category_evaluation_json(text):
    try:
        json_obj = json.loads(text)
        category_evaluation = json_obj["category_evaluation"]
        if (len(category_evaluation) <= 3):
            return None
        # print(f"Got category_evaluation: {str(category_evaluation)}")
        good_categories = 0
        bad_categories = 0
        good_category_evaluations = {}
        for category, perc in category_evaluation.items():
            if not isinstance(category, str) or (not isinstance(perc, int) and not isinstance(perc, float)):
                bad_categories += 1
                print(f"Bad field: {str(category)} : {str(perc)}")
            else:
                good_category_evaluations[category.lower()] = perc
                if category not in picked_categories:
                    bad_categories += 1
                    print(f"Bad category: {str(category)} : {str(perc)}")
                else:
                    good_categories += 1
        return good_category_evaluations
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {text}: {e}")
    except Exception as e:
        print(f"Error reading file {text}: {e}")
    return None

def parse_defect_evaluation_json(text):
    try:
        json_obj = json.loads(text)
        defect_evaluation = json_obj["defect_evaluation"]
        if (len(defect_evaluation) < 3):
            return None
        good_categories = 0
        bad_categories = 0
        good_defect_evaluations = {}
        defect_categories = ['good solution', 'wrong solution', 'compilation error', 'runtime error']
        for category, perc in defect_evaluation.items():
            if not isinstance(category, str) or (not isinstance(perc, int) and not isinstance(perc, float)):
                bad_categories += 1
                print(f"Bad field: {str(category)} : {str(perc)}")
            else:
                good_defect_evaluations[category.lower()] = perc
                category = category.lower() if category.lower() != 'good_solution' else 'good solution'
                category = category if category != 'wrong_solution' else 'wrong solution'
                category = category if category != 'compilation_error' else 'compilation error'
                category = category if category != 'runtime_error' else 'runtime error'
                if category.lower() not in defect_categories and category.lower() not in picked_categories:
                    bad_categories += 1
                    print(f"Bad category: {str(category)} : {str(perc)}")
                else:
                    good_categories += 1
        return good_defect_evaluations
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {text}: {e}")
    except Exception as e:
        print(f"Error reading file {text}: {e}")
    return None

def fill_category_evaluation(file_path, messages):
    response = get_request(messages)
    category_evaluation = parse_category_evaluation_json(response)
    if category_evaluation is not None:
        print("Final category_evaluation: " + str(category_evaluation))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            data['category_evaluation'] = category_evaluation
            pass
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
                pass

        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")


def fill_defect_evaluation(file_path, messages, is_gpt_4):
    response = get_request(messages, is_gpt_4)
    defect_evaluation = parse_defect_evaluation_json(response)
    if defect_evaluation is not None:
        print("Final defect_evaluation: " + str(defect_evaluation))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print("Actually is: " + data['verdict']+ " is gpt4= "+ str(is_gpt_4))
            if is_gpt_4 == False: 
                data[defect_eval_ver] = defect_evaluation
            else:
                data[defect_eval_gpt4_ver] = defect_evaluation
            pass
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
                pass

        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")

def do_category_evaluations(container: helper.ProblemSolutionContainer, packs: List[helper.ProblemPack]):
    for pack in packs:
        problem_obj = container.problems[pack.problem_id]
        if ("category_evaluation" not in problem_obj):
            messages =[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": "I will give some categories and a programming task."
                "Your job is to give a percentage value from 0 to 100, which indicates how much that category describes the programming task I'm gonna give."
                "Give the answer in a JSON format containing a field category_evaluation, which is a map with category keys and the percentage values."
                f"Give the JSON only, nothing else, no other text. \nHere are the categories: {str(picked_categories)} \nHere is the programming task: {problem_obj['desc']}"}
            ]
            fill_category_evaluation(container.problem_paths[pack.problem_id], messages)
        else:
            print(f"Already Done category evaluation: {problem_obj['contestId']}")
        for solution_id in pack.solution_ids:
            solution_obj = container.solutions[solution_id]
            if ("category_evaluation" not in solution_obj):
                messages =[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": "I will give some categories and a program."
                "Your job is to give a percentage value from 0 to 100, which indicates how much that category describes the program I'm gonna give."
                "Give the answer in a JSON format containing a field category_evaluation, which is a map with category keys and the percentage values."
                f"Give the JSON only, nothing else, no other text. \nHere are the categories: {str(picked_categories)} \nHere is the program: {solution_obj['source']}"}
                ]  
                fill_category_evaluation(container.solution_paths[solution_id], messages)
            else:
                print(f"Already Done category evaluation: {problem_obj['contestId']} : {solution_obj['id']}")
        
def do_defect_evaluations(container: helper.ProblemSolutionContainer, packs: List[helper.ProblemPack], is_gpt_4 = False):
    for pack in packs:
        problem_obj = container.problems[pack.problem_id]
        for solution_id in pack.solution_ids:
            solution_obj = container.solutions[solution_id]
            if ((is_gpt_4 == False and defect_eval_ver not in solution_obj) or (is_gpt_4 == True and defect_eval_gpt4_ver not in solution_obj)):
                messages =[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": "I will give a programming task and a program."
                "Your job is to evaluate the solution for the problem for these 4 categories: {'good solution', 'wrong solution', 'compilation error', 'runtime error'}."
                "Give a percentage value from 0 to 100, which indicates the seperate chances of the solution beeing a 'good solution' or a 'wrong solution' or that it produces a 'compilation error' or produces a 'runtime error' for the given problem."
                "The 4 percentages dont have to sum to 100."
                "Give the answer in a JSON format containing a field defect_evaluation, which is a map with category keys and the percentage values."
                f"Give the JSON only, nothing else, no other text. \nHere is the problem: {problem_obj['desc']} \nHere is the program: {solution_obj['source']}"}
                ]  
                fill_defect_evaluation(container.solution_paths[solution_id], messages, is_gpt_4)
            else:
                print(f"Already Done defect evaluation: {problem_obj['contestId']} : {solution_obj['id']}")
        

def count_filed_category_evaluation(probs_sols):
    return len([probs_sol for probs_sol in probs_sols if 'category_evaluation' in probs_sol])

def count_filed_defect_evaluation(probs_sols):
    return len([probs_sol for probs_sol in probs_sols if defect_eval_ver in probs_sol])

def count_filed_defect_evaluation_gpt_4(probs_sols):
    return len([probs_sol for probs_sol in probs_sols if defect_eval_gpt4_ver in probs_sol])

def main():
    problems = helper.problem_getter()
    problem_paths = helper.problem_path_iterator(lambda _, full_path, _3: full_path)

    problem_suggested_categories_count = count_filed_suggested_categories(problems)
    print(f"Already created suggested categories for problems: {problem_suggested_categories_count}")

    solutions = helper.solution_getter()
    solution_paths = helper.solution_path_iterator(lambda _, full_path, _3: full_path)
    problem_solution_container = helper.ProblemSolutionContainer(problems, problem_paths, solutions, solution_paths)

    solution_suggested_categories_count = count_filed_suggested_categories(solutions)
    print(f"Already created suggested categories for solutions: {solution_suggested_categories_count}")

    problem_category_evaluation_count = count_filed_category_evaluation(problems)
    print(f"Already filled categories for problems: {problem_category_evaluation_count}")

    solution_category_evaluation_count = count_filed_category_evaluation(solutions)
    print(f"Already filled categories for solutions: {solution_category_evaluation_count}")

    defect_evaluation_count = count_filed_defect_evaluation(solutions)
    print(f"Already filled defect evaluations: {defect_evaluation_count}")

    defect_evaluation_gpt_4_count = count_filed_defect_evaluation_gpt_4(solutions)
    print(f"Already filled defect gpt4 evaluations: {defect_evaluation_gpt_4_count}")

    # fill_suggested_categories(200 - problem_suggested_categories_count, problems, problem_paths, "problem")

    # fill_suggested_categories(200 - solution_suggested_categories_count, solutions, solution_paths, "solution")

    #problem_packs = pick_problem_packs(problem_solution_container, 15, 10, 5, 30)
    problem_packs = pick_problem_packs(problem_solution_container, 1, 10, 9, 10)

    do_category_evaluations(problem_solution_container, problem_packs)

    do_defect_evaluations(problem_solution_container, problem_packs, False)

if __name__ == "__main__":
    main()