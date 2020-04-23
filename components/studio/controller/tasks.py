from registrar.celery import app


def on_alliance_save_spawn_aggregator():
    pass


def on_alliance_delete_destroy_aggregator():
    pass


def on_model_save_notify_aggregator():
    pass


def on_member_save_notify_aggregator():
    pass


def on_endpoint_save_notify_aggregator():
    pass


def member_request_contribution():
    pass


def member_request_validation():
    pass


from registrar.celery import app

#TODO remove?
@app.task
def train_remote(node_id):
    import subprocess
    import os
    cmd = "python3 train.py"
    args = "--node-id={}".format(node_id)
    cwd = os.cwd()
    subprocess.run(cmd, args, cwd=cwd)
