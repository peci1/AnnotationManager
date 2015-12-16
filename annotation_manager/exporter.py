from abc import ABCMeta, abstractmethod

from annotation_manager.plugin import PluginMetaclass


class AnnotationExporter(object):
    """
    Exporter of annotations.

    Instances of descendants of this class should always belong to one particular destination.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        super(AnnotationExporter, self).__init__()

    @abstractmethod
    def add_annotations(self, annotations):
        """Add annotations to the corresponding source.

        :param AnnotationSet annotations: The set of annotations to add.
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


