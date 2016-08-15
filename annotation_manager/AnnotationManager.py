import imp
import logging
import os
import pkgutil
import sys

from annotation_manager.exporter import AnnotationExporterFactory
from annotation_manager.importer import AnnotationImporterFactory
from annotation_manager.common_representation import DocumentLibrary

logging.basicConfig()

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AnnotationManager(object):
    """
    A library serving as manager/synchronizer of annotations/highlight/notes between different devices and programs.

    It primarily targets PDF files in connection with PDF/ebook readers, but is open to extensions to other domains.
    """

    _source = None
    _destination = None

    _source_library = None
    _destination_library = None

    _source_importer = None
    _destination_importer = None
    _exporter = None

    def __init__(self, source=None, destination=None):
        super(AnnotationManager, self).__init__()

        this_script_path = os.path.dirname(os.path.realpath(__file__))
        additional_plugin_dirs = [
            # ./annotation_manager/plugins
            os.path.join(this_script_path, "plugins"),
            # ~/.annotation_manager/plugins
            os.path.join(os.environ["HOME"], ".annotation_manager", "plugins"),
        ]

        AnnotationManager.load_plugins(*additional_plugin_dirs)

        self._importer_factories = []
        self._exporter_factories = []

        if hasattr(AnnotationImporterFactory, "registered"):
            for factory in AnnotationImporterFactory.registered:
                self.add_importer_factory(factory)

        if hasattr(AnnotationExporterFactory, "registered"):
            for factory in AnnotationExporterFactory.registered:
                self.add_exporter_factory(factory)

        self.import_source(source)
        self.import_destination(destination)

    def get_source_library(self):
        if self._source_library is None and self._source_importer is not None:
            self._source_library = self._source_importer.get_annotated_library()

        return self._source_library

    def get_destination_library(self):
        if self._destination_library is None and self._destination_importer is not None:
            self._destination_library = self._destination_importer.get_annotated_library()

        return self._destination_library

    def import_source(self, source):
        if source is not None:
            self._source = source
            for factory in self._importer_factories:
                importer = factory.get_importer_for_source(self._source)
                if importer is not None:
                    self._source_importer = importer
                    break

    def import_destination(self, destination):
        if destination is not None:
            self._destination = destination
            for factory in self._importer_factories:
                importer = factory.get_importer_for_source(self._destination)
                if importer is not None:
                    self._destination_importer = importer
                    break
            for factory in self._exporter_factories:
                exporter = factory.get_exporter_for_destination(self._destination)
                if exporter is not None:
                    self._exporter = exporter
                    break

    def sync_and_export_annotations(self):
        source_library = self.get_source_library()
        destination_library = self.get_destination_library()

        common, only_source, only_destination = source_library.find_common_documents(destination_library)

        for (source_document, destination_document) in common:
            common_annotations, only_source_annotations, only_destination_annotations = \
                source_document.find_common_annotations(destination_document)

            self._exporter.add_annotations_to_document(destination_document, only_source_annotations)

    def add_importer_factory(self, factory):
        """
        Register a new :py:class:`AnnotationImporterFactory`.

        :param factory: The factory to register.
        :type factory: AnnotationImporterFactory
        """
        assert issubclass(factory, AnnotationImporterFactory)
        log.info("Importing %s" % str(factory))
        self._importer_factories.append(factory())

    def add_exporter_factory(self, factory):
        """
        Register a new :py:class:`AnnotationExporterFactory`.

        :param factory: The factory to register.
        :type factory: AnnotationExporterFactory
        """
        assert issubclass(factory, AnnotationExporterFactory)
        log.info("Importing %s" % str(factory))
        self._exporter_factories.append(factory())

    @staticmethod
    def load_plugins(*paths):
        """
        Register all plugins from the given paths.

        Currently, plugins mean :py:class:`AnnotationImporterFactory` and :py:class:`AnnotationExporterFactory`.
        :param paths: Paths to the plugin directories.
        :type paths: basestring
        """
        paths = list(paths)

        for _, name, _ in pkgutil.iter_modules(paths):
            fid, pathname, desc = imp.find_module(name, paths)
            try:
                imp.load_module(name, fid, pathname, desc)
            except Exception as e:
                log.warning("could not load plugin module '%s': %s",
                                pathname, e.message)
            if fid:
                fid.close()
