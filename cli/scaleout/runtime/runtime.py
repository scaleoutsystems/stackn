from scaleout.project import Project


class Runtime(Project):
    """ Base class for a scaleout platform runtime client. """

    def __init__(self, cwd=None, config_file=None):
        # The config file is read by the Project constructor
        super(Runtime, self).__init__(cwd, config_file)

