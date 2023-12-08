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


def clean_files():
    solution_path_iterator(lambda _, full_path, _3: delete_non_json(full_path))
    problem_path_iterator(lambda _, full_path, _3: delete_non_json(full_path))


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