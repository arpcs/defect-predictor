import agents
from helper import clean_files
from codeforces_problem_fetcher import runner, try_fun
from functools import partial

def main():
    problems = helper.problem_getter()
    solutions = helper.solution_getter()

    print(f"All Number of problems: {len(problems)} \t Number of solutions : {len(solutions)}")

    if len(problems) < 1000 or len(solutions) < 20000:
        print("running with 100 problems each with 100 solutions")
        try_fun(partial(runner, 100, 100))
        print("running with 1000 problems each with 10 solutions")
        try_fun(partial(runner, 1000, 10))
    else:
        print("Limit passed. Skipping soultion and problem fetching.")

    print("Cleaning files, preprocessing")
    clean_files()

if __name__ == "__main__":
    main()