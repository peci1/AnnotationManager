import hashlib
import os
from abc import ABCMeta, abstractmethod

from collections import OrderedDict

from pdfloc_converter.converter import PDFLocConverter
from pdfloc_converter.pdfloc import PDFLocBoundingBoxes


class DocumentLibrary(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        self._documents = OrderedDict()

    def add_documents(self, **documents):
        for path, document in documents.items():
            assert isinstance(document, AnnotatedDocument)
            self._documents[path] = document

    def get_documents(self):
        """Return a list of all documents in this library.

        :return: A list of all documents in this library.
        :rtype: list of :py:class:`AnnotatedDocument`
        """
        return tuple(self._documents.values())

    def get_document_by_path(self, path):
        """Return the document instance corresponding to the given filesystem path.

        :param basestring|unicode path: Filesystem path of the document.
        :return: The document instance, or None if the document is not found.
        :rtype: :py:class:`AnnotatedDocument`
        """
        return self._documents[path] if path in self._documents else None

    def find_common_documents(self, other):
        assert isinstance(other, DocumentLibrary)
        return find_common_items(self.get_documents(), other.get_documents(), lambda document: document.filesize)


class AnnotatedDocument(object):

    __metaclass__ = ABCMeta

    _filename = None
    _filesize = None
    _full_path = None
    _filehashes = {'md5': None, 'sha1': None}

    def __init__(self, full_path, filesize):
        super(AnnotatedDocument, self).__init__()
        self._full_path = full_path
        self._filename = full_path.split(os.sep)[-1]
        self._filesize = filesize

    @abstractmethod
    def get_annotations(self):
        """Return the set of annotations for this document.

        :return: The set of annotations.
        :rtype: :py:class:`AnnotationSet`
        """
        pass

    def find_common_annotations(self, other_document, convert_to_bboxes=True):
        assert isinstance(other_document, AnnotatedDocument)

        my_annotations = self.get_annotations()
        other_annotations = other_document.get_annotations()

        if my_annotations.empty() and other_annotations.empty():
            return [], my_annotations, other_annotations

        if convert_to_bboxes:
            if len(my_annotations.bbox_annotations) == 0:
                pdfloc_to_bboxes(self, my_annotations)
            if len(other_annotations.bbox_annotations) == 0:
                pdfloc_to_bboxes(other_document, other_annotations)

            return find_common_items(my_annotations.bbox_annotations, other_annotations.bbox_annotations,
                                     lambda annotation: annotation.page)
        else:
            if len(my_annotations.pdfloc_annotations) == 0:
                bboxes_to_pdfloc(self, my_annotations)
            if len(other_annotations.pdfloc_annotations) == 0:
                bboxes_to_pdfloc(other_document, other_annotations)

            return find_common_items(my_annotations.pdfloc_annotations, other_annotations.pdfloc_annotations,
                                     lambda annotation: annotation.page)

    def __eq__(self, other):
        if not isinstance(other, AnnotatedDocument):
            return NotImplemented

        if other.filesize != self.filesize:
            return False

        if other.filename == self.filename:
            return True

        for hash_method, hash in self._filehashes.items():
            if hash is not None and hash_method in other._filehashes and other._filehashes[hash_method] is not None:
                return hash == other._filehashes[hash_method]

        self._filehashes['sha1'] = hashlib.sha1(open(self.full_path, 'rb').read()).hexdigest()
        other._filehashes['sha1'] = hashlib.sha1(open(other.full_path, 'rb').read()).hexdigest()

        return self._filehashes['sha1'] == other._filehashes['sha1']

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def full_path(self):
        return self._full_path

    @property
    def filename(self):
        return self._filename

    @property
    def filesize(self):
        return self._filesize


class AnnotationSet(object):

    __metaclass__ = ABCMeta

    _pdfloc_annotations = []
    _bbox_annotations = []

    def empty(self):
        return len(self._pdfloc_annotations) == 0 and len(self._bbox_annotations) == 0

    @property
    def pdfloc_annotations(self):
        return self._pdfloc_annotations

    @property
    def bbox_annotations(self):
        return self._bbox_annotations

    def __str__(self):
        return self.__repr__()

    def __repr__(self):

        if len(self._pdfloc_annotations) > 0:
            return u"\n".join([str(annotation) for annotation in self._pdfloc_annotations])

        if len(self._bbox_annotations) > 0:
            return u"\n".join([str(annotation) for annotation in self._bbox_annotations])

        return "No annotations."


def find_common_items(list1, list2, key_function):
    list1_items = {}
    list2_items = {}

    only_1 = []
    only_2 = []
    common = []

    for item in list1:
        key = key_function(item)
        if key not in list1_items:
            list1_items[key] = []
        list1_items[key].append(item)

    for item in list2:
        key = key_function(item)
        if key not in list2_items:
            list2_items[key] = []
        list2_items[key].append(item)

    keys_1 = set(list1_items.keys())
    keys_2 = set(list2_items.keys())

    for key in keys_1 - keys_2:
        only_1.extend(list1_items[key])
    for key in keys_2 - keys_1:
        only_2.extend(list2_items[key])
    for key in keys_1 & keys_2:
        for item_1 in list1_items[key]:
            for item_2 in list2_items[key]:
                if item_1 == item_2:
                    common.append((item_1, item_2))

    return common, only_1, only_2


def pdfloc_to_bboxes(document, annotations):
    converter = PDFLocConverter(document.full_path, pdflocs=annotations.pdfloc_annotations)
    converter.parse_document()
    for pdfloc in annotations.pdfloc_annotations:
        annotations.bbox_annotations.append(PDFLocBoundingBoxes(
            converter.pdfloc_pair_to_bboxes(pdfloc), pdfloc.start.page, pdfloc.comment)
        )


def bboxes_to_pdfloc(document, annotations):
    converter = PDFLocConverter(document.full_path, bboxes=annotations.bbox_annotations)
    converter.parse_document()
    for bbox in annotations.bbox_annotations:
        annotations.pdfloc_annotations.append(converter.bboxes_to_pdfloc_pair(bbox))
