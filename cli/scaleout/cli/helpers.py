import sys
from prettytable import PrettyTable
import click
import uuid


def prompt(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def _print_table(resource, names, keys):
    x = PrettyTable()
    x.field_names = names
    for item in resource:
        row = [item[k] for k in keys]
        x.add_row(row)
    print(x)

def create_table(ctx, resource, names, keys):
    client = ctx.obj['CLIENT']
    objects = client.create_list(resource)
    _print_table(objects, names, keys)

def search_for_model(ctx, resource, name):
    client = ctx.obj['CLIENT']
    objects = client.create_list(resource)
    model_exists = False
    for item in objects:
        if item['name'] == name:
            model_exists = True
    return model_exists
 
def new_id(run_id):
    new_id = input("A log object with ID = {} already exists in 'src/models/tracking' directory. \n".format(run_id) \
                 + "Please provide a unique ID for the current run or press enter to use a randomly generated ID: ")
    if new_id:
        confirmed = False
        question = "Do you want to assign this training run with the ID '{}'?".format(new_id)
        while not confirmed:
            confirmed = prompt(question)
            if confirmed:
                return new_id
            else:
                new_id = input("Assign a new unique ID or press enter to assign a random ID: ")
                print(new_id)
                if not new_id:
                    break
    new_id = str(uuid.uuid1().hex)
    return new_id

class Determinant(click.Option):
    def __init__(self, *args, **kwargs):
        self.determinant = kwargs.pop('determinant')
        assert self.determinant, "'determinant' parameter required"
        super(Determinant, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        unallowed_present = self.name in opts
        determinant_present = self.determinant in opts
        if determinant_present:
            if unallowed_present:
                raise click.UsageError("Illegal usage: Cannot pass a value for '{}' together with '{}' when running 'stackn train'".format(self.name, self.determinant))
            else:
                self.prompt = None
        return super(Determinant, self).handle_parse_result(ctx, opts, args)