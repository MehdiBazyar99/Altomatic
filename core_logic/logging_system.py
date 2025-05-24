from PyQt6.QtCore import QObject, pyqtSignal

class Logger(QObject):
    new_message = pyqtSignal(str, str) # Define signal: message, level

    def __init__(self):
        super().__init__()

    def info(self, msg):
        # print(f"[INFO] {msg}")
        self.new_message.emit(f"{msg}", "info")

    def warn(self, msg):
        # print(f"[WARN] {msg}")
        self.new_message.emit(f"{msg}", "warn")

    def error(self, msg):
        # print(f"[ERROR] {msg}")
        self.new_message.emit(f"{msg}", "error")

    def debug(self, msg):
        # print(f"[DEBUG] {msg}")
        self.new_message.emit(f"{msg}", "debug")

    def token(self, msg):
        # print(f"[TOKEN] {msg}")
        self.new_message.emit(f"{msg}", "token")
