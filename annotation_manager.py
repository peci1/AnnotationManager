#!/usr/bin/env python
import sys

from annotation_manager.AnnotationManager import AnnotationManager


class AnnotationManagerCLI(object):

    def __init__(self):
        super(AnnotationManagerCLI, self).__init__()

        self.manager = AnnotationManager()

    def execute_commandline(self, argv):
        pass

if __name__ == '__main__':
    # run CLI
    cli = AnnotationManagerCLI()
    sys.exit(cli.execute_commandline(sys.argv))
