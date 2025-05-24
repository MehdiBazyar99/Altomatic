from PyQt6.QtCore import QObject, pyqtSignal
from core_logic.logic import process_images # Make sure this path is correct

class ProcessingWorker(QObject):
    finished = pyqtSignal(dict)  # To emit the summary_result dictionary
    error = pyqtSignal(str)      # To emit error messages

    def __init__(self, logger, state):
        super().__init__()
        self.logger = logger
        self.state = state

    def run(self):
        try:
            self.logger.info("Processing worker started.")
            summary_result = process_images(self.logger, self.state)
            if summary_result:
                self.finished.emit(summary_result)
            else:
                self.error.emit("Processing returned no result.")
        except Exception as e:
            self.logger.error(f"Exception in processing worker: {e}")
            self.error.emit(str(e))
        finally:
            self.logger.info("Processing worker run method finished.")
