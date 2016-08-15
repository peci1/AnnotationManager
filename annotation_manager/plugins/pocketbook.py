import os
import hashlib
import re
from collections import OrderedDict

from annotation_manager.importer import AnnotationImporterFactory, AnnotationImporter
from annotation_manager.common_representation import AnnotatedDocument, DocumentLibrary, AnnotationSet
from pdfloc_converter.pdfloc import PDFLocPair


class AnnotationStorage(object):
    _annotations_dir = None

    def __init__(self, annotations_dir):
        super(AnnotationStorage, self).__init__()

        self._annotations_dir = annotations_dir

    def get_annotation_file(self, document_file):
        assert isinstance(document_file, PocketbookAnnotatedDocument)

        return "%s%s%s_A_%s.html" % (self._annotations_dir, os.sep, document_file.filename, document_file.file_hash)

    def get_annotation_dir(self, document_file):
        assert isinstance(document_file, PocketbookAnnotatedDocument)

        return "%s%s%s_A_%s.files" % (self._annotations_dir, os.sep, document_file.filename, document_file.file_hash)


class PocketbookDocumentLibrary(DocumentLibrary):

    _system_drive_path = None
    _external_drive_path = None
    _annotations_dir = None

    _annotation_storage = None
    _document_roots = []

    def __init__(self, system_drive_path, annotations_dir, external_drive_path=None):
        super(PocketbookDocumentLibrary, self).__init__()

        self._system_drive_path = system_drive_path
        self._external_drive_path = external_drive_path
        self._annotations_dir = annotations_dir

        self._annotation_storage = AnnotationStorage(self._annotations_dir)

        self._document_roots.append(self._system_drive_path)
        if self._external_drive_path is not None:
            self._document_roots.append(self._external_drive_path)

        self._seek_for_documents()

    def _seek_for_documents(self):
        documents = OrderedDict()

        for root in self._document_roots:
            for dirpath, _, filenames in os.walk(root):
                for filename in filenames:
                    if filename.endswith(".pdf") or filename.endswith(".PDF"):
                        document = PocketbookAnnotatedDocument(filename, dirpath, self._annotation_storage)
                        documents[document.full_path] = document

        self.add_documents(**documents)


class PocketbookAnnotatedDocument(AnnotatedDocument):

    _dir = None
    _annotation_storage = None

    _file_hash = None

    _pdfloc_regex = r'<!-- type="32" level="1" position="(#pdfloc\([^)]+\))" endposition="(#pdfloc\([^)]+\))" --!>'
    _pdfloc_comment_regex = r'<font color="#000000" size="3" face="Arial">(.*)</font><br>'

    def __init__(self, document_file, document_dir, annotation_storage):
        assert isinstance(annotation_storage, AnnotationStorage)

        full_path = document_dir + os.sep + document_file
        filesize = os.path.getsize(full_path)

        super(PocketbookAnnotatedDocument, self).__init__(full_path, filesize)

        self._dir = document_dir
        self._annotation_storage = annotation_storage

    @property
    def dir(self):
        return self._dir

    @property
    def file_hash(self):
        if self._file_hash is None:
            # the file hash is computed as md5(first_4096_bytes | last_4096_bytes | file_size)
            h = hashlib.md5()
            with open(self.full_path, 'rb') as f:
                # hash the first 4096 bytes
                h.update(f.read(4096))

                # hash the last 4096 bytes
                f.seek(-4096, os.SEEK_END)
                h.update(f.read(4096))

                # hash file length
                f.seek(0, os.SEEK_END)
                size = f.tell()
                h.update("%i" % size)

            self._file_hash = h.hexdigest()
            self._filehashes['md5pb'] = self._file_hash

        return self._file_hash

    def get_annotations(self):
        annotations_file = self._annotation_storage.get_annotation_file(self)

        annotations = []

        with open(annotations_file, 'r') as f:
            line = f.readline()
            while len(line) > 0:
                match = re.match(self._pdfloc_regex, line)
                if match is not None:
                    start = match.group(1)
                    end = match.group(2)
                    comment = None

                    # the comment is stored two lines further
                    line = f.readline()
                    if len(line) > 0:
                        line = f.readline()
                        if len(line) > 0:
                            comment_match = re.match(self._pdfloc_comment_regex, line)
                            if comment_match is not None:
                                comment = comment_match.group(1)

                    annotations.append(PDFLocPair(start, end, comment))

                line = f.readline()

        return PocketbookAnnotationSet(self, annotations)


class PocketbookAnnotationSet(AnnotationSet):

    _document = None

    def __init__(self, document, annotations):
        super(PocketbookAnnotationSet, self).__init__()

        self._document = document
        self._pdfloc_annotations = annotations


class PocketbookAnnotationImporter(AnnotationImporter):

    _system_drive_path = None
    _external_drive_path = None
    _annotations_dir = None

    _library = None

    def __init__(self, system_drive_path, annotations_dir, external_drive_path=None):
        super(PocketbookAnnotationImporter, self).__init__()

        self._system_drive_path = system_drive_path
        self._external_drive_path = external_drive_path
        self._annotations_dir = annotations_dir

    def get_annotated_library(self):
        if self._library is None:
            self._library = PocketbookDocumentLibrary(self._system_drive_path, self._annotations_dir,
                                                      self._external_drive_path)

        return self._library


class PocketbookImporterFactory(AnnotationImporterFactory):

    def get_importer_for_source(self, source):
        if not isinstance(source, str) and not isinstance(source, unicode):
            return None

        source_parts = source.split(os.pathsep)
        if not (2 <= len(source_parts) <= 3):
            return None

        if source_parts[0] != "pocketbook":
            return None

        system_path = source_parts[1]
        external_path = source_parts[2] if len(source_parts) == 3 else None

        if not os.path.exists(system_path):
            return None

        if external_path is not None and not os.path.exists(external_path):
            # not a critical problem if external storage is defined but not found
            external_path = None

        annotations_dir = os.path.join(system_path, 'system', 'config', 'Active Contents')
        if not os.path.exists(annotations_dir):
            return None

        return PocketbookAnnotationImporter(system_path, annotations_dir, external_path)
