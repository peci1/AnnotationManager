#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import os
import sys

from annotation_manager.AnnotationManager import AnnotationManager

if __name__ == '__main__':
    this_script_path = unicode(os.path.dirname(os.path.realpath(__file__)), sys.getfilesystemencoding())

    pocketbook_path = os.path.join(this_script_path, u'resources', u'pocketbook')

    source = u"pocketbook%s%s%s%s%s%s" % (
        os.pathsep, os.path.join(pocketbook_path, u"system"), os.sep,
        os.pathsep, os.path.join(pocketbook_path, u"external"), os.sep
    )

    manager = AnnotationManager(source=source, destination=u"mendeley")
    manager.sync_and_export_annotations()
