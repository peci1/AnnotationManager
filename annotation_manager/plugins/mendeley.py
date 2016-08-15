from __future__ import print_function

import os
import sys
import sqlite3
import uuid
from datetime import datetime
import urllib

from pdfloc_converter.pdfloc import BoundingBoxOnPage, PDFLocBoundingBoxes
from annotation_manager.common_representation import DocumentLibrary, AnnotatedDocument, AnnotationSet
from annotation_manager.exporter import AnnotationExporterFactory, AnnotationExporter
from annotation_manager.importer import AnnotationImporterFactory, AnnotationImporter


"""
In order for this plugin to work on Windows, you must replace your Python/DLLs/sqlite3.dll with the
newest version from http://www.sqlite.org/download.html .
"""


class MendeleyDocumentLibrary(DocumentLibrary):

    _sqlite_connection = None
    _sqlite_cursor = None

    _documents = {}

    def __init__(self, sqlite_connection):
        super(MendeleyDocumentLibrary, self).__init__()

        self._sqlite_connection = sqlite_connection
        self._sqlite_cursor = cursor = sqlite_connection.cursor()

        cursor.execute("SELECT df.documentId,df.hash,f.localUrl "
                       "FROM DocumentFiles df JOIN Files f ON df.hash=f.hash "
                       "WHERE unlinked='false' AND f.localUrl!=''")
        result = cursor.fetchall()

        documents = {}
        for row in result:
            document_id = row[0]
            file_hash = row[1]
            file_url = row[2]

            try:
                document = MendeleyAnnotatedDocument(document_id, file_hash, file_url, cursor)
                documents[document.full_path] = document
            except Exception as e:
                print(e)
                print(file_url)

        self.add_documents(**documents)


class MendeleyAnnotatedDocument(AnnotatedDocument):

    _document_id = None
    _file_hash = None
    _file_url = None
    _full_path = None
    _sqlite_cursor = None

    def __init__(self, document_id, file_hash, file_url, sqlite_cursor):
        full_path = urllib.unquote(file_url.encode('ascii')[len("file:///"):]).replace("//", "/").decode('utf-8')
        if sys.platform.startswith(u"win32"):
            full_path = full_path.replace(u"/", u"\\")

        filesize = os.path.getsize(full_path)

        super(MendeleyAnnotatedDocument, self).__init__(full_path, filesize)

        self._document_id = document_id
        self._file_hash = file_hash
        self._file_url = file_url
        self._sqlite_cursor = sqlite_cursor

        self._filehashes['sha1'] = file_hash

    @property
    def document_id(self):
        return self._document_id

    @property
    def file_hash(self):
        return self._file_hash

    def get_annotations(self):
        self._sqlite_cursor.execute("SELECT h.id,h.createdTime,hr.id,hr.page,hr.x1,hr.y1,hr.x2,hr.y2 "
                                    "FROM FileHighlights h JOIN FileHighlightRects hr ON h.id=hr.highlightId "
                                    "WHERE h.unlinked='false' AND h.documentId=?", (self._document_id,))

        result = self._sqlite_cursor.fetchall()

        highlights = {}
        for row in result:
            highlight_id = row[0]
            created_time = row[1]
            rectangle_id = row[2]
            page = row[3]
            bbox = row[4:8]

            bbox_on_page = BoundingBoxOnPage(bbox, page)

            if highlight_id not in highlights:
                highlights[highlight_id] = PDFLocBoundingBoxes([bbox_on_page])
            else:
                highlights[highlight_id].bboxes.append(bbox_on_page)

        return MendeleyAnnotationSet(self, list(highlights.values()))


class MendeleyAnnotationSet(AnnotationSet):

    _document = None

    def __init__(self, document, annotations):
        super(MendeleyAnnotationSet, self).__init__()

        self._document = document
        self._bbox_annotations = annotations


class MendeleyAnnotationImporter(AnnotationImporter):

    _sqlite_path = None

    _library = None

    def __init__(self, sqlite_path):
        super(MendeleyAnnotationImporter, self).__init__()

        self._sqlite_path = sqlite_path

    def get_annotated_library(self):
        if self._library is None:
            self._library = MendeleyDocumentLibrary(sqlite3.connect(self._sqlite_path))

        return self._library


class MendeleyImporterFactory(AnnotationImporterFactory):

    def get_importer_for_source(self, source):
        sqlite_full_path = MendeleyPlugin.location_to_sqlite_path(source)
        if sqlite_full_path is None:
            return None

        return MendeleyAnnotationImporter(sqlite_full_path)


class MendeleyPlugin(object):

    @staticmethod
    def location_to_sqlite_path(location):

        if not isinstance(location, unicode):
            return None

        location_parts = location.split(os.pathsep)
        if not (1 <= len(location_parts) <= 2):
            return None

        if location_parts[0] != u"mendeley":
            return None

        data_dir = location_parts[1] if len(location_parts) >= 2 and len(location_parts[1]) > 0 else None
        if data_dir is None:
            if sys.platform.startswith("win32"):
                data_dir = os.path.expandvars(u"%LOCALAPPDATA%\\Mendeley Ltd.\\Mendeley Desktop")
            elif sys.platform.startswith("linux"):
                data_dir = os.path.expandvars(u"$HOME/.local/share/data/Mendeley Ltd./Mendeley Desktop")
            elif sys.platform.startswith("darwin"):
                data_dir = os.path.expandvars(u"$HOME/Library/Application Support/Mendeley Desktop")
            else:
                return None

        if not os.path.exists(data_dir):
            return None

        sqlite_file = (location_parts[2] + u"@www.mendeley.com.sqlite") \
            if len(location_parts) >= 3 and len(location_parts[2]) > 0 \
            else u"online.sqlite"

        sqlite_full_path = os.path.join(data_dir, sqlite_file)

        if not os.path.exists(sqlite_full_path):
            if sqlite_file == u"online.sqlite":
                sqlite_file = None
                for file in os.listdir(data_dir):
                    if file != "monitor.sqlite" and file.endswith(".sqlite"):
                        sqlite_file = file
                        sqlite_full_path = os.path.join(data_dir, sqlite_file)
                        break
            if sqlite_file is None:
                return None

        # check the SQLite3 header
        with open(sqlite_full_path, "rb") as db_file:
            db_header = db_file.read(16).encode('hex')
            db_file.close()
            # see http://www.sqlite.org/fileformat.html#database_header magic header string
            if db_header != "53514c69746520666f726d6174203300":
                return None

        return sqlite_full_path


class MendeleyExporterFactory(AnnotationExporterFactory):
    def get_exporter_for_destination(self, destination):
        sqlite_full_path = MendeleyPlugin.location_to_sqlite_path(destination)
        if sqlite_full_path is None:
            return None

        return MendeleyExporter(sqlite_full_path)


class MendeleyExporter(AnnotationExporter):

    def __init__(self, sqlite_path):
        super(MendeleyExporter, self).__init__()

        self._sqlite_path = sqlite_path

    def export_library(self, library):
        pass

    def add_annotations_to_document(self, document, annotations):
        assert isinstance(document, MendeleyAnnotatedDocument)

        with sqlite3.connect(self._sqlite_path) as connection:
            cursor = connection.cursor()

            document_id = document.document_id
            pdf_hash = document.file_hash
            date = self.get_current_date_string()

            for annotation in annotations:
                assert isinstance(annotation, PDFLocBoundingBoxes)
                guid = self.create_guid()

                cursor.execute(
                    "INSERT INTO `FileHighlights` VALUES "
                    "(NULL,'',(?),(?),(?),(?),'false', '#fff5ad', 'adcca408-5f3d-33d5-8303-8fdf105bd938');",  # TODO
                    (guid, document_id, pdf_hash, date)
                )

                annotation_id = cursor.lastrowid

                cursor.execute("INSERT INTO `RemoteFileHighlights` VALUES ('%s','ObjectCreated',0);" % guid)

                for bbox in annotation.bboxes:
                    cursor.execute(
                        "INSERT INTO `FileHighlightRects` VALUES "
                        "(NULL,(?),(?),(?),(?),(?),(?));",
                        (annotation_id, bbox.page, bbox.bbox[0], bbox.bbox[1], bbox.bbox[2], bbox.bbox[3])
                    )

    @staticmethod
    def create_guid():
        return str(uuid.uuid4())

    @staticmethod
    def get_current_date_string():
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
