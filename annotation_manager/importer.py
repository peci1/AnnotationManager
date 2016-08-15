from abc import ABCMeta, abstractmethod

from annotation_manager.plugin import PluginMetaclass


class AnnotationImporter(object):
    """
    Importer of annotations.

    Instances of descendants of this class should always belong to one particular source.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        super(AnnotationImporter, self).__init__()

    @abstractmethod
    def get_annotated_library(self):
        """Get the imported :py:class:`DocumentLibrary`.

        :return: The imported :py:class:`DocumentLibrary`.
        :rtype: DocumentLibrary
        """
        pass


class AnnotationImporterFactory(object):
    """
    Factory for :py:class:`AnnotationImporter`s.
    """

    __metaclass__ = PluginMetaclass

    def __init__(self):
        super(AnnotationImporterFactory, self).__init__()

    @abstractmethod
    def get_importer_for_source(self, source):
        """
        Get an :py:class:`AnnotationImporter` for the given source, or None if this factory doesn't handle the given
        type of sources.

        :param source: The source to create importer for.
        :type source: Any
        :return: The corresponding :py:class:`AnnotationImporter`, or None if the importer cannot be created.
        :rtype: AnnotationImporter
        """
        pass


