#!/usr/bin/env python
# coding=utf-8
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

    manager = AnnotationManager(source=source)

    library = manager.get_source_library()
    path = os.path.join(pocketbook_path, u"system", u"books", u"Škola", u"Clanky",
                                         u"Abdolmaleki et al. - Model-Based Relative Entropy Stochastic "
                                         u"Search - 2015.pdf")
    document = library.get_document_by_path(path)

    annotations = document.get_annotations()

    print annotations
