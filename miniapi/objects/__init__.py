from miniapi.objects.data import DataObjects
from miniapi.objects.interface_wrapper import InterfaceWrapperObjects


class Objects(
    DataObjects,
    InterfaceWrapperObjects
):

    def __init__(self, app):
        self.app = app
