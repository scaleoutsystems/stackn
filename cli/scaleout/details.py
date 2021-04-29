import platform
import psutil
import logging
import json
import os
import sys
from scaleout.cli.helpers import prompt

def get_system_details(info):
    try:
        info['Platform'] = platform.system()
        #info['Platform version'] = platform.version()
        info['Architecture'] = platform.machine()
        info['Processor'] = platform.processor()
        info['RAM'] = str(round(psutil.virtual_memory().total / (1024.0 **3))) + " GB"
        info['Python version'] = platform.python_version()
        json_prep = json.dumps(info)
        return json.loads(json_prep)
    except Exception as e:
        print("Failed to retrieve details about your system.")
        logging.exception(e)


def get_cpu_details(info):
    try:
        info['Physical cores'] = psutil.cpu_count(logical=False)
        info['Total cores'] = psutil.cpu_count(logical=True)
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            info[f'Core {i}'] = f'{percentage}%'
        info['Total CPU usage'] = f'{psutil.cpu_percent()}%'
        json_prep = json.dumps(info)
        return json.loads(json_prep)
    except Exception as e:
        print("Failed to retrieve details about the CPU of your machine.")
        logging.exception(e)


# Function that pauses the run until the user either commits changed files in the repo, or tells the program to contnue training with uncommitted files
# ---------------- Question -------------------
# Should all files be committed before training or is it enough if the user commits some files in the repo?
# ---------------------------------------------
def commit_helper(repo, exit_message): # This function needs to be tested and modified. Might note even be necessary to have this function
    print('WARNING: Uncommitted files exist in the current Git repository. Training the model with uncommitted files '\
        + 'should be avoided for major experiments since this will negatively impact code versioning. To increase future ' \
        + 'reproducibility of your experiment, please consider committing all files before training the model.\n')
    valid = ["1", "2"]
    while True:
        answer = input("What do you want to do? \n" \
                       + " 1) Continue training the model without committing my files (Not recommended). \n"\
                       + " 2) Put the training session on hold to commit my files (Highly recommended). \n"\
                       + "Choose an option [1 or 2]: ")
        if answer in valid:
            break
        else:
            print("\nPlease respond with '1' or '2'. \n")
    if answer == "1": 
        print("\nThe training session will continue with uncommitted files in the repo. This might affect the reproducibility of your experiment.")
        question = "Are you sure you want to continue?"
        confirmed = prompt(question)
        if confirmed:
            return False
        else:
            sys.exit(exit_message.format("commit your files"))
    else: 
        # The user wants to commit files before continuing model training. 
        # We could let the user add and commit files here with a subprocess operation? E.g. subprocess.run("git add .", check=True, shell=True)
        answer = input("\nA good choice! After you commit your files, press enter to continue training the model "\
                       + "(or abort the current training session by pressing arbitrary key): ")
        if answer:        
            sys.exit(exit_message.format("commit your files"))
        else: # Would be good to check here whether the files have been committed successfully. Maybe the user does not want to commit all files?
            print("Perfect, your files have been committed and the training session will continue.")
            #while True:
            #    if not repo.is_dirty():
                    
            #        break
            #    else:
        return True


def get_git_details(code_version):
    exit_message = "Aborting this training session. Please {} before running 'stackn train' again."
    try: 
        import git
    except ImportError:
        print('Failed to import Git')
        return None
    try:
        # current_repo = git.Repo(os.getcwd()) # Which one of these should we use? Needs testing
        current_repo = git.Repo(search_parent_directories=True)
        is_committed = True
        if current_repo.is_dirty(): # This should be true if uncommitted files exist
            is_committed = commit_helper(current_repo, exit_message)
        latest_commit = current_repo.head.object.hexsha
        print("Code version {} will be tied to the Git commit hash '{}'.".format(code_version, latest_commit))
        if not is_committed:
            print("Since uncommitted files exist in the current repo, it will be noted in the training log that the code " \
                + "used to train the model in this run does not correspond to the recorded commit hash. " \
                + "This is done mainly for the purpose of appropriate code versioning and future reproducibility.")
    except (git.InvalidGitRepositoryError, ValueError):
        latest_commit = "No recent Git commit to log"
        if git.InvalidGitRepositoryError:
            print('WARNING: Failed to extract Git repo. Check to see if you are currently working in a Git repository.')
            question = "Do you want to continue training the model anyways (not recommended)?"
            confirmed = prompt(question)
            if confirmed:
                current_repo = "No Git repository to log"
            else: 
                sys.exit(exit_message.format('enter an active Git repo'))
        elif ValueError and not committed_files:
            print("WARNING: Failed to extract latest Git commit hash. No commits seem to have been made yet and you have chosen not to commit them. " \
                + "The training session will continue.")
    return (current_repo, latest_commit)


def get_run_details(code_version):
    system_details = get_system_details({})
    cpu_details = get_cpu_details({})
    git_details = get_git_details(code_version)
    return system_details, cpu_details, git_details
