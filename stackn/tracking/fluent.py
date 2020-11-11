#class ActiveRun(Run):
#    def __init__(self, run):
#        Run.__init__(self, run.info, run.data)


def start_run():
    print("Start run and do something")

def end_run():
    print("End run and do something")
    
def active_run():
    print("Get active run and do something")

def log_param(key, value):
    print("log parameter")

def log_metric(key, value):
    print("Log metric")