import imp
import logging
import os
import pkgutil
import sys

from annotation_manager.exporter import AnnotationExporterFactory
from importer import AnnotationImporterFactory

logging.basicConfig()

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AnnotationManager(object):
    """
    A library serving as manager/synchronizer of annotations/highlight/notes between different devices and programs.

    It primarily targets PDF files in connection with PDF/ebook readers, but is open to extensions to other domains.
    """

    def __init__(self):
        super(AnnotationManager, self).__init__()

        this_script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        additional_plugin_dirs = [
            os.path.join(this_script_path, "annotation_manager", "plugins"),  # ./annotation_manager/plugins
            os.path.join(os.environ["HOME"], ".annotation_manager"),  # ~/.annotation_manager
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

    def add_importer_factory(self, factory):
        """
        Register a new :py:class:`AnnotationImporterFactory`.

        :param factory: The factory to register.
        :type factory: AnnotationImporterFactory
        """
        assert issubclass(factory, AnnotationImporterFactory)
        log.info("Importing %s" % str(factory))
        self._importer_factories.append(factory)

    def add_exporter_factory(self, factory):
        """
        Register a new :py:class:`AnnotationExporterFactory`.

        :param factory: The factory to register.
        :type factory: AnnotationExporterFactory
        """
        assert issubclass(factory, AnnotationExporterFactory)
        log.info("Importing %s" % str(factory))
        self._exporter_factories.append(factory)

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
