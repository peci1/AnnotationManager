#!/usr/bin/env python
# coding=utf-8
import os

import sys

from annotation_manager.AnnotationManager import AnnotationManager

if __name__ == '__main__':
    manager = AnnotationManager(source=u"mendeley")

    library = manager.get_source_library()
    path = os.path.join(u"D:\\", u"Dokumenty", u"Mendeley Desktop",
                        u"Abdolmaleki et al. - Model-Based Relative Entropy Stochastic Search - 2015.pdf")
    document = library.get_document_by_path(path)

    annotations = document.get_annotations()

    print annotations
