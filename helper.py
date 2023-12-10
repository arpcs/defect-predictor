import os
import json
import shutil

# Directory path for the 'content' folder
problems_path = 'codeforces_problems'

def problem_path_iterator(callback):
  ret = []
  for problem_pack_name in os.listdir(problems_path):
    problem_pack_path = os.path.join(problems_path, problem_pack_name)
    if not os.path.isfile(problem_pack_name):
      for name in os.listdir(problem_pack_path):
        full_path = os.path.join(problem_pack_path, name)
        if not os.path.isfile(full_path):
          full_file_path = os.path.join(full_path, "problem.txt")
          ret.append(callback(problem_pack_name, full_file_path, name))
  return ret

def solution_path_iterator(callback):
  ret = []
  for problem_pack_name in os.listdir(problems_path):
    problem_pack_path = os.path.join(problems_path, problem_pack_name)
    for root, dirs, files in os.walk(problem_pack_path):
        for file in files:
            if file != 'problem.txt':
              full_path = os.path.join(root, file)
              ret.append(callback(problem_pack_name, full_path, file))
  return ret

def deleter(file_path):
    # Check if the path exists
    if os.path.exists(file_path):
        # Check if it's a file
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"File {file_path} has been deleted.")
        # Check if it's a directory
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
            print(f"Directory {file_path} has been deleted.")
    else:
        print(f"The path {file_path} does not exist.")

def read_json(file_path):
  try:
    with open(file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
        return json_data
  except Exception as e:
    print(f"Err file[{file_path}]: " + str(e))
  return None

def delete_non_json(file_path):
  try:
    with open(file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
  except Exception as e:
    print(f"Err file[{file_path}]: " + str(e))
    print("Deleting..")
    filename = os.path.basename(file_path)
    root_directory = os.path.dirname(file_path)
    if filename == "problem.txt" and not os.path.exists(file_path):
        deleter(root_directory)
    else:
        deleter(file_path)
  return None

def problem_getter():
  ret = problem_path_iterator(lambda _, full_path, _3: read_json(full_path))
  return ret

def solution_getter():
  ret = solution_path_iterator(lambda _, full_path, _3: read_json(full_path))
  return ret

def fix_fields(file_path):
  try:
    with open(file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
        new_data = {}
        changed = False
        for field, val  in json_data['defect_evaluation_gpt4_v4'].items():
            newfield = field.lower()
            newfield = newfield if newfield != "good_solution" else "good solution"
            newfield = newfield if newfield != "wrong_solution" else "wrong solution"
            newfield = newfield if newfield != "compilation_error" else "compilation error"
            newfield = newfield if newfield != "runtime_error" else "runtime error"
            new_data[newfield] = val
            if newfield != field.lower():
                changed = True
        if changed:
            json_data['defect_evaluation_gpt4_v4'] = new_data
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, indent=4)
                    pass

            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {file_path}")
            except Exception as e:
                print(f"An error occurred: {e}")
  except Exception as e:
    pass
  return None

def clean_files():
    solution_path_iterator(lambda _, full_path, _3: delete_non_json(full_path))
    problem_path_iterator(lambda _, full_path, _3: delete_non_json(full_path))
    solution_path_iterator(lambda _, full_path, _3: fix_fields(full_path))
    solution_path_iterator(lambda _, full_path, _3: delete_non_json(full_path))
    problem_path_iterator(lambda _, full_path, _3: delete_non_json(full_path))

class ProblemPack:
    def __init__(self, problem_id, solution_ids):
        self.problem_id = problem_id  # ID for the problem
        self.solution_ids = solution_ids  # List of solution IDs

    def add_solution(self, solution_id):
        """Add a solution ID to the problem pack."""
        self.solution_ids.append(solution_id)

    def remove_solution(self, solution_id):
        """Remove a solution ID from the problem pack if it exists."""
        if solution_id in self.solution_ids:
            self.solution_ids.remove(solution_id)

    def get_problem_id(self):
        """Return the problem ID."""
        return self.problem_id

    def get_solution_ids(self):
        """Return the list of solution IDs."""
        return self.solution_ids

    def __str__(self):
        """Return a string representation of the problem pack."""
        return f"Problem ID: {self.problem_id}, Solution IDs: {self.solution_ids}"


class ProblemSolutionContainer:
    def __init__(self, problems, problem_paths, solutions, solution_paths):
        self.problems = problems
        self.solutions = solutions
        self.problem_paths = problem_paths
        self.solution_paths = solution_paths
        self.problem_id_to_solutions = self._map_problem_to_solutions()
        self.problem_id_to_problem = self._map_problem_id_to_problem()

    def _map_problem_to_solutions(self):
        mapping = {}
        for index, solution in enumerate(self.solutions):
            problem_id = (solution['problem']['contestId'], solution['problem']['index'])
            mapping.setdefault(problem_id, []).append(index)

        return mapping

    def _map_problem_id_to_problem(self):
        mapping = {}
        for index, problem in enumerate(self.problems):
            problem_id = (problem['contestId'], problem['index'])
            mapping[problem_id] = index
        return mapping

    def get_solutions_for_problem(self, problem_id):
        return self.problem_id_to_solutions.get((self.problems[problem_id]['contestId'],self.problems[problem_id]['index']), [])

    def get_problem_for_solution(self, solution_id):
        return self.problem_id_to_problem.get((self.solutions[solution_id]['problem']['contestId'], self.solutions[solution_id]['problem']['index']), None)

    def get_self(self):
        return self

def main():
    print("Cleaning Files")
    clean_files()
    print("Cleaning Done")

    # Iterating through each file in the directory
    for folder_name in os.listdir(problems_path):
        problem_pack_path = os.path.join(problems_path, folder_name)
        if not os.path.isfile(folder_name):
            problem_count = len([name for name in os.listdir(problem_pack_path) if not os.path.isfile(os.path.join(problem_pack_path, name))])
            solution_count = 0
            for root, dirs, files in os.walk(problem_pack_path):
                for file in files:
                    if file != 'problem.txt':
                        solution_count += 1
            print(f"In the folder \'{folder_name}\'\t Number of problems: {problem_count}")


    num_of_problems = len(problem_path_iterator(lambda _, _2, _3: 1))
    num_of_solutions = len(solution_path_iterator(lambda _, _2, _3: 1))
    print(f"All Number of problems: {num_of_problems} \t Number of solutions : {num_of_solutions}")

    problems = problem_getter()
    solutions = solution_getter()

    print(f"All Number of problems: {len(problems)} \t Number of solutions : {len(solutions)}")

if __name__ == "__main__":
    main()

