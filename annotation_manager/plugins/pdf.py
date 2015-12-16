from annotation_manager.exporter import AnnotationExporterFactory, AnnotationExporter


class PdfExporterFactory(AnnotationExporterFactory):
    def get_exporter_for_destination(self, destination):
        if not isinstance(destination, basestring) and not isinstance(destination, unicode):
            return None

        return PdfExporter(destination)


class PdfExporter(AnnotationExporter):

    def __init__(self, path):
        super(PdfExporter, self).__init__()

        self._path = path

    def add_annotations(self, annotations):
        pass