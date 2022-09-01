from PyQt6.QtWidgets import QMainWindow

from bundle import bundle_dir


class Runtime:
    _instance = None

    _gui: bool = False
    _main_window: QMainWindow
    _version: str

    @property
    def gui(self):
        return self._gui

    @gui.setter
    def gui(self, status: bool):
        self._gui = status

    @property
    def main_window(self):
        return self._main_window

    @main_window.setter
    def main_window(self, window: QMainWindow):
        self._main_window = window

    @property
    def version(self):
        return self._version

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Runtime, cls).__new__(cls)

            with open(bundle_dir + '/version.txt', 'r') as fh:
                cls._version = fh.read().strip()

        return cls._instance


runtime = Runtime()
