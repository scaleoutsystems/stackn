import platform
import psutil
import logging
import json
import os

def get_system_info(info):
    try:
        info['platform'] = platform.system()
        info['platform_version'] = platform.version()
        info['architecture'] = platform.machine()
        info['processor'] = platform.processor()
        info['ram'] = str(round(psutil.virtual_memory().total / (1024.0 **3))) + " GB"
        return json.dumps(info)
    except Exception as e:
        logging.exception(e)

def get_cpu_info(info):
    try:
        info['physical_cores'] = psutil.cpu_count(logical=False)
        info['total_cores'] = psutil.cpu_count(logical=True)
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            info[f'core_{i}'] = f'{percentage}%'
        info['total_cpu_usage'] = f'{psutil.cpu_percent()}%'
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
        repo = git.Repo(os.getcwd())
        sha = repo.head.object.hexsha
        latest_commit_timestamp = repo.head.commit.committed_datetime
        is_committed = repo.is_dirty()
        if not is_committed:
            print("WARNING: Uncommitted files exist in current git repository.")
        return [repo, sha, latest_commit_timestamp]
    except (git.InvalidGitRepositoryError, git.GitCommandNotFound, git.NoSuchPathError, ValueError):
        print('WARNING: Failed to exctract Git info. This could be due to the working directory not being a git repository. Run "git init" and create a first commit')
        return []

"""    
def get_git_commit():
    #path = 'adamhagevall/stackn/cli/setup.py'
    try:
        import git
        print('Inside')
    except ImportError as e:
        _logger.warning(
            "Failed to import Git (the Git executable is probably not on your PATH),"
            " so Git SHA is not available. Error: %s",
            e,
        )
        #return None
        print('Fail 1')
    try:
        if os.path.isfile(path):
            path = os.path.dirname(path)
            print(path)
        repo = git.Repo(path, search_parent_directories=True)
        commit = repo.head.commit.hexsha
        print(commit)
        #return commit
    except (git.InvalidGitRepositoryError, git.GitCommandNotFound, ValueError, git.NoSuchPathError):
        print('Fail 2')
        #return None
    print('Test successful')
"""