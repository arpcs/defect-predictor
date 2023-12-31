import requests
import os
import time
import codeforces_parser
import shutil
import json
import random
from functools import partial
import re

#PROBLEM_LINK = 'https://codeforces.com/problemset/problem/'
#CONTEST_LINK = 'https://codeforces.com/contest/1906/submission/236201276'
def create_submission_link(id, submission):
    return f'https://codeforces.com/contest/{str(id)}/submission/{str(submission)}'
def create_problem_link(id, index):
    return f'https://codeforces.com/problemset/problem/{str(id)}/{str(index)}'

def get_already_existing_problems(problems, number_of_solutions):
    folder_name = os.path.join("codeforces_problems",f"x{number_of_solutions}")
    result = []
    for root, dirs, files in os.walk(folder_name):
        for folder in dirs:
            for i, problem in enumerate(problems, start=1):
                if folder == f"problem_{problem['contestId']}_{problem['index']}":
                    result.append(problem)
    return result

def get_problems(number_of_problems, number_of_solutions):
    url = "https://codeforces.com/api/problemset.problems"

    max_attempts = 20
    attempts = 0
    response = None
    while attempts < max_attempts:
        try:
            response = requests.get(url)
            time.sleep(2)
            if response.status_code == 200 and response.json()["status"] == "OK":
                break
            else:
                attempts += 1
                print(f"Attempt {attempts}: Failed to fetch problems. Retrying...")
                time.sleep(2 + attempts * attempts / 10)
        except requests.RequestException as e:
            attempts += 1
            print(f"Attempt {attempts}: Error occurred in problems: {e}. Retrying...")
            time.sleep(2 + attempts * attempts / 10)
    
    problems = None
    if response.json()["status"] == "OK":
        problems = response.json()["result"]["problems"]
    old_problems = get_already_existing_problems(problems, number_of_solutions)
    random_old =  random.sample(old_problems, min(len(old_problems), number_of_problems))
    random_new = random.sample(problems, min(len(problems), number_of_problems))
    result = (random_old + random_new)[:number_of_problems]
    return result
    #return response.json()["result"]["problems"][:number_of_problems]

def get_all_solutions(contest_id, count):
    url = f"https://codeforces.com/api/contest.status?contestId={contest_id}&from=1&count={max(1, count)}"

    max_attempts = 20
    attempts = 0
    response = None
    while attempts < max_attempts:
        try:
            response = requests.get(url)
            time.sleep(2)
            if response.status_code != 200 or response.json()["status"] != "OK":
                attempts += 1
                print(f"Attempt {attempts}: Failed to fetch solutions. Retrying...")
                time.sleep(2 + attempts * attempts / 10)
            else:
                break
        except requests.RequestException as e:
            attempts += 1
            print(f"Attempt {attempts}: Error occurred in solutions: {e}. Retrying...")
            time.sleep(2 + attempts * attempts / 10)
    
    submissions = response.json()["result"]
    return submissions

def get_solutions(all_solutions, problem_id, verdict, num):
    solutions = [s for s in all_solutions if s.get("problem", {}).get("index") == problem_id and s.get("verdict") == verdict]
    #return solutions[-num:]
    return random.sample(solutions, min(len(solutions), num))


def get_solution_number_w_verdict(folder_name, verdict):
    verdict_num = 0
    solution_folder_name = os.path.join(f"{folder_name}","solutions")
    for root, dirs, files in os.walk(solution_folder_name):
        for file in files:
            with open(os.path.join(root, file), 'r') as file:
                try:
                    data = json.load(file)
                    if data['verdict'] == verdict:
                        verdict_num += 1
                except json.JSONDecodeError:
                    pass
    return verdict_num

def runner(number_of_problems, number_of_solutions):
    problems = get_problems(number_of_problems, number_of_solutions)

    contests_solutions = {}
    for i, problem in enumerate(problems, start=1):
        contests_solutions[problem['contestId']] = None

    
    print(f"Found {len(contests_solutions)} number of problem groups")


    for i, problem in enumerate(problems, start=1):
        folder_name = os.path.join("codeforces_problems",f"x{number_of_solutions}",f"problem_{problem['contestId']}_{problem['index']}")
        os.makedirs(folder_name, exist_ok=True)

        good_verdicts = ["FAILED", "OK", "PARTIAL", "COMPILATION_ERROR", "RUNTIME_ERROR", "WRONG_ANSWER"]
        all_verdicts = ["FAILED", "OK", "PARTIAL", "COMPILATION_ERROR", "RUNTIME_ERROR", "WRONG_ANSWER", "PRESENTATION_ERROR", "TIME_LIMIT_EXCEEDED", "MEMORY_LIMIT_EXCEEDED", "IDLENESS_LIMIT_EXCEEDED", "SECURITY_VIOLATED", "CRASHED", "INPUT_PREPARATION_CRASHED", "CHALLENGED", "SKIPPED", "TESTING", "REJECTED"]

        sum_of_already_done = 0
        for verdict in good_verdicts:
            already_done = get_solution_number_w_verdict(folder_name, verdict)
            sum_of_already_done += already_done
        if sum_of_already_done >= number_of_solutions:
            print(f"Already done this problem! {sum_of_already_done}/{number_of_solutions} for  {problem['contestId']} {problem['index']}")
            continue
        print(f"Fetching more for {problem['contestId']} {problem['index']} already done: {sum_of_already_done}/{number_of_solutions}")

        if contests_solutions[problem['contestId']] is None:
            contests_solutions[problem['contestId']] = get_all_solutions(problem["contestId"], number_of_solutions * 400)
            print(f"For problem group [{problem['contestId']}] found {len(contests_solutions[problem['contestId']])} number of solutions")

        all_solutions = contests_solutions[problem['contestId']]
        print(f"Solutions for [{problem['contestId']} - {problem['index']}]")           
        for verdict in good_verdicts:
            solutions = get_solutions(contests_solutions[problem['contestId']], problem["index"], verdict,  number_of_solutions * 400)
            print(f"\t{verdict} = {len(solutions)}")
        
        for retries in range(20):
            try:
                if not os.path.exists(f"{folder_name}/problem.txt"):
                    link = create_problem_link(problem['contestId'], problem['index'])
                    problem['desc'] = codeforces_parser.parse_problem(link)
                    with open(f"{folder_name}/problem.txt", "w") as file:
                        json.dump(problem, file, indent=4)
                        break
            except Exception as e:
                if retries >= 19:
                    print(f"Error processing problem data: {problem['contestId']}, {problem['index']} : {e}. \nGiving up")
                    #shutil.rmtree(folder_name)
                else:
                    print(f"Error processing problem data: {problem['contestId']}, {problem['index']} : {e}. \nRetry [{retries}]")
                time.sleep(2 + retries*retries / 10)


        currently_fetched = 0
        solution_couter_sum = 0
        for verdict in good_verdicts:
            num_to_fetch = int(number_of_solutions / 2 if verdict == "OK" else number_of_solutions / 10)
            if verdict == "WRONG_ANSWER":
                num_to_fetch = number_of_solutions - currently_fetched

            solutions = get_solutions(all_solutions, problem["index"], verdict, num_to_fetch * 400)
            currently_fetched += min(len(solutions), num_to_fetch)

            solution_couter = 0
            already_done = get_solution_number_w_verdict(folder_name, verdict)
            solution_couter += already_done
            if solution_couter >= num_to_fetch:
                print(f"\t\tfor {verdict} already DONE {already_done} \t satisfying the limit: {num_to_fetch}")
                solution_couter_sum += solution_couter
                continue

            bad_couter = 0
            for j, solution in enumerate(solutions, start=1):
                solution_folder_name = os.path.join(f"{folder_name}","solutions")
                os.makedirs(solution_folder_name, exist_ok=True)
                solution_file_name = os.path.join(solution_folder_name,f"solution_{solution['id']}.txt")
                try:
                    if not os.path.exists(solution_file_name):
                        with open(solution_file_name, "w") as file:
                            link = create_submission_link(problem['contestId'], solution['id'])
                            solution['source'] = codeforces_parser.parse_solution(link)
                            json.dump(solution, file, indent=4)
                    solution_couter += 1
                    bad_couter = 0
                except Exception as e:
                    #print(f"Error processing solution data: {e}. \nDeleting solution")
                    os.remove(solution_file_name)
                    bad_couter += 1
                    if bad_couter > 40:
                        print("Too many bad request leaving solution")
                        break
                    if bad_couter % 10 == 0:
                        print(f"Bad solution requests: {bad_couter}")
                    time.sleep(2 + bad_couter * bad_couter / 40)
                if solution_couter >= num_to_fetch:
                    break
                
            print(f"\t\tfor {verdict} \t done {solution_couter}\t[{already_done}]\t out of \t{num_to_fetch}")
            solution_couter_sum += solution_couter
        is_good = "Good" if number_of_solutions <= solution_couter_sum else "Bad"
        print(f"{is_good}: Overall done {solution_couter_sum} out of {number_of_solutions}")

def try_fun(fun):
    attempts = 0
    while attempts < 40:
        try:
            fun()
            break  # Break out of the loop if the function succeeds
        except Exception as e:
            attempts += 1
            print(f"Main fun throwed. retrying ({attempts}). error: {e}")
            if attempts == 40:
                print(f"Too many retries. Main fun throwed: error:{e} ")
                raise e  # Rethrow the exception on the 40th attempt


def main():
    print("running with 10 problems each with 10 solutions")
    try_fun(partial(runner, 10, 10))
    print("running with 100 problems each with 100 solutions")
    try_fun(partial(runner, 100, 100))
    print("running with 1000 problems each with 10 solutions")
    try_fun(partial(runner, 1000, 10))

if __name__ == "__main__":
    main()