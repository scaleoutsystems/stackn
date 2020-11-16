import platform
import psutil
import logging
import json
import os

def get_system_info(info):
    try:
        info['Platform'] = platform.system()
        #info['Platform version'] = platform.version()
        info['Architecture'] = platform.machine()
        info['Processor'] = platform.processor()
        info['RAM'] = str(round(psutil.virtual_memory().total / (1024.0 **3))) + " GB"
        return json.dumps(info)
    except Exception as e:
        logging.exception(e)

def get_cpu_info(info):
    try:
        info['Physical cores'] = psutil.cpu_count(logical=False)
        info['Total cores'] = psutil.cpu_count(logical=True)
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            info[f'Core {i}'] = f'{percentage}%'
        info['Total CPU usage'] = f'{psutil.cpu_percent()}%'
        return json.dumps(info)
    except Exception as e:
        logging.exception(e)

def get_git_info():
    try: 
        import git
    except ImportError:
        print('Failed to import Git')
        return []
    try:
        current_repo = git.Repo(os.getcwd())
        latest_commit = current_repo.head.object.hexsha
        latest_commit_timestamp = current_repo.head.commit.committed_datetime
        is_committed = current_repo.is_dirty()
        if not is_committed:
            print("WARNING: Uncommitted files exist in current Git repository.")
        return [current_repo, latest_commit, latest_commit_timestamp]
    except (git.InvalidGitRepositoryError, git.GitCommandNotFound, git.NoSuchPathError, ValueError):
        print('WARNING: Failed to extract Git info. This could be due to the working directory not being a Git repository.')
        return []
