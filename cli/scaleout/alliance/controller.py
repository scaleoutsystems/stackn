from scaleout.alliance.client import MemberRuntimeClient

import logging

logger = logging.getLogger(__name__)

from scaleout.utils.dispatcher import Dispatcher


class Controller(Dispatcher):

    def __init__(self, project):
        super(Controller, self).__init__(project)
        self.project = project
        self.c = None

    def client(self):
        self.c = MemberRuntimeClient()
        self.c.run()

    def train(self, ):
        self.run_cmd('train')

    def validate(self, ):
        self.run_cmd('validate')

    def predict(self, ):
        self.run_cmd('predict')
