from abc import ABCMeta, abstractmethod

from annotation_manager.plugin import PluginMetaclass
from annotation_manager.common_representation import DocumentLibrary


class AnnotationExporter(object):
    """
    Exporter of annotations.

    Instances of descendants of this class should always belong to one particular destination.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        super(AnnotationExporter, self).__init__()

    @abstractmethod
    def export_library(self, library):
        """Export document library to the corresponding destination.

        :param DocumentLibrary library: The library to export.
        """
        pass

    @abstractmethod
    def add_annotations_to_document(self, document, annotations):
        """Add a set of new annotations to a document.

        :param AnnotatedDocument document: The document.
        :param annotations: A list of annotations to add.
        :type annotations: list of PDFLocPair|PDFLocBoundingBoxes
        """
        pass


class AnnotationExporterFactory(object):
    """
    Factory for :py:class:`AnnotationExporter`s.
    """

    __metaclass__ = PluginMetaclass

    def __init__(self):
        super(AnnotationExporterFactory, self).__init__()

    @abstractmethod
    def get_exporter_for_destination(self, destination):
        """
        Get an :py:class:`AnnotationExporter` for the given destination, or None if this factory doesn't handle the
        given type of destinations.

        :param destination: The destination to create exporter for.
        :type destination: Any
        :return: The corresponding :py:class:`AnnotationExporter`, or None if the exporter cannot be created.
        :rtype: AnnotationExporter
        """
        pass


