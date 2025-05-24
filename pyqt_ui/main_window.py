import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QTabWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QFileDialog,
    QFormLayout, QCheckBox, QProgressBar, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QUrl, QThread # Added QThread
from PyQt6.QtGui import QColor, QAction, QPixmap

# Altomatic Core Logic Imports
from config import load_config, save_config, DEFAULT_CONFIG, open_config_folder, reset_config
from core_logic.logging_system import Logger
from core_logic.logic import process_images
from .worker import ProcessingWorker # Import the worker

# Token Cost Constant
GPT_NANO_TOKEN_COST_PER_1K = 0.002

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Altomatic PyQt6")
        self.setGeometry(100, 100, 800, 700) 
        self.thread = None # Initialize thread attribute

        # Main content container
        main_widget = QWidget()
        self.main_layout = QVBoxLayout(main_widget) 
        
        self.menu_bar = self.menuBar() 
        help_menu = self.menu_bar.addMenu("&Help")
        
        self.setCentralWidget(main_widget)

        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.input_tab = QWidget()
        self.output_tab = QWidget()
        self.settings_tab = QWidget()

        self.tabs.addTab(self.input_tab, "Input")
        self.tabs.addTab(self.output_tab, "Output")
        self.tabs.addTab(self.settings_tab, "Settings")

        self._setup_input_tab()
        self._setup_output_tab()
        self._setup_settings_tab()

        self.process_button = QPushButton("Describe Images")
        self.main_layout.addWidget(self.process_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFixedHeight(150)
        self.main_layout.addWidget(self.log_display)

        self.session_tokens_label = QLabel("Session Tokens: 0")
        self.main_layout.addWidget(self.session_tokens_label)
        self.total_tokens_label = QLabel("Total Accumulated Tokens: 0")
        self.main_layout.addWidget(self.total_tokens_label)
        self.estimated_cost_label = QLabel("Estimated Session Cost: $0.0000")
        self.main_layout.addWidget(self.estimated_cost_label)

        self.logger = Logger()
        self.user_config = load_config()
        self.themes_dir = os.path.join(os.path.dirname(__file__), "themes") 
        
        self.logger.new_message.connect(self.append_log_message)
        self.logger.info("User configuration loaded.")
        
        about_action = QAction("About Altomatic", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        self._populate_ui_from_config() 

        self.process_button.clicked.connect(self.start_image_processing)
        self.save_settings_button.clicked.connect(self.save_current_settings) 
        self.reset_total_tokens_button.clicked.connect(self.reset_accumulated_tokens_count)
        self.open_config_folder_button.clicked.connect(self.handle_open_config_folder)
        self.reset_defaults_button.clicked.connect(self.handle_reset_defaults)
        self.theme_combo.currentTextChanged.connect(self.apply_theme)

    def _setup_input_tab(self):
        layout = QVBoxLayout(self.input_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        input_type_layout = QHBoxLayout()
        input_type_label = QLabel("Input Type:")
        self.input_type_combo = QComboBox()
        self.input_type_combo.addItems(["Folder", "File"])
        input_type_layout.addWidget(input_type_label)
        input_type_layout.addWidget(self.input_type_combo)
        layout.addLayout(input_type_layout)
        input_path_layout = QHBoxLayout()
        input_path_label = QLabel("Input Path:")
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Drag & Drop or Browse...")
        self.input_path_edit.setAcceptDrops(True)
        self.input_path_edit.dragEnterEvent = self.dragEnterEvent
        self.input_path_edit.dropEvent = self.dropEvent
        self.browse_button = QPushButton("Browse...")
        input_path_layout.addWidget(input_path_label)
        input_path_layout.addWidget(self.input_path_edit)
        input_path_layout.addWidget(self.browse_button)
        layout.addLayout(input_path_layout)
        self.image_count_label = QLabel("0 image(s) selected")
        layout.addWidget(self.image_count_label)
        
        self.image_preview_label = QLabel("Image Preview")
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setFixedSize(250, 250) 
        self.image_preview_label.setStyleSheet("QLabel { border: 1px solid gray; }")
        layout.addWidget(self.image_preview_label)

        self.browse_button.clicked.connect(self.browse_input_path)
        self.input_path_edit.textChanged.connect(self.update_image_count)
        self.input_type_combo.currentIndexChanged.connect(self.update_image_count)
        self.input_tab.setLayout(layout)
        self.update_image_count() # Initial call

    def _setup_output_tab(self):
        layout = QVBoxLayout(self.output_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        save_to_layout = QHBoxLayout()
        save_to_label = QLabel("Save to:")
        self.output_folder_combo = QComboBox()
        self.output_folder_combo.addItems(["Same as input", "Pictures", "Desktop", "Custom"])
        save_to_layout.addWidget(save_to_label)
        save_to_layout.addWidget(self.output_folder_combo)
        layout.addLayout(save_to_layout)
        custom_folder_layout = QHBoxLayout()
        custom_folder_label = QLabel("Custom Folder:")
        self.custom_output_path_edit = QLineEdit()
        self.browse_output_button = QPushButton("Browse...")
        custom_folder_layout.addWidget(custom_folder_label)
        custom_folder_layout.addWidget(self.custom_output_path_edit)
        custom_folder_layout.addWidget(self.browse_output_button)
        layout.addLayout(custom_folder_layout)
        self.custom_output_path_edit.setEnabled(False)
        self.browse_output_button.setEnabled(False)
        self.output_folder_combo.currentIndexChanged.connect(self.update_output_custom_path_state)
        self.browse_output_button.clicked.connect(self.browse_custom_output_folder)
        self.output_tab.setLayout(layout)

    def _setup_settings_tab(self):
        layout = QFormLayout(self.settings_tab)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow(QLabel("OpenAI API Key:"), self.api_key_edit)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "BlueGray", "Solarized", "Pinky"])
        layout.addRow(QLabel("UI Theme:"), self.theme_combo)
        self.filename_lang_combo = QComboBox()
        self.filename_lang_combo.addItems(["English", "Persian"])
        layout.addRow(QLabel("Filename Language:"), self.filename_lang_combo)
        self.alttext_lang_combo = QComboBox()
        self.alttext_lang_combo.addItems(["English", "Persian"])
        layout.addRow(QLabel("Alt Text Language:"), self.alttext_lang_combo)
        self.name_detail_combo = QComboBox()
        self.name_detail_combo.addItems(["Minimal", "Normal", "Detailed"])
        layout.addRow(QLabel("Name Detail Level:"), self.name_detail_combo)
        self.vision_detail_combo = QComboBox()
        self.vision_detail_combo.addItems(["low", "high", "auto"])
        layout.addRow(QLabel("Image Vision Detail:"), self.vision_detail_combo)
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItem("gpt-4.1-nano")
        layout.addRow(QLabel("AI Model:"), self.ai_model_combo)
        self.ocr_enabled_checkbox = QCheckBox("Enable OCR")
        layout.addRow(self.ocr_enabled_checkbox)
        hbox_tesseract = QHBoxLayout()
        self.tesseract_path_edit = QLineEdit()
        self.browse_tesseract_button = QPushButton("Browse...")
        hbox_tesseract.addWidget(self.tesseract_path_edit)
        hbox_tesseract.addWidget(self.browse_tesseract_button)
        layout.addRow(QLabel("Tesseract Path:"), hbox_tesseract)
        self.browse_tesseract_button.clicked.connect(self.browse_tesseract_path)
        self.ocr_language_edit = QLineEdit()
        self.ocr_language_edit.setPlaceholderText("eng")
        layout.addRow(QLabel("OCR Language:"), self.ocr_language_edit)
        action_buttons_layout = QHBoxLayout()
        self.save_settings_button = QPushButton("Save Settings")
        self.reset_defaults_button = QPushButton("Reset Defaults")
        self.open_config_folder_button = QPushButton("Open Config Folder")
        self.reset_total_tokens_button = QPushButton("Reset Accumulated Tokens")
        action_buttons_layout.addWidget(self.save_settings_button)
        action_buttons_layout.addWidget(self.reset_defaults_button)
        action_buttons_layout.addWidget(self.open_config_folder_button)
        action_buttons_layout.addWidget(self.reset_total_tokens_button)
        layout.addRow(action_buttons_layout)
        self.settings_tab.setLayout(layout)

    def _populate_ui_from_config(self):
        self.input_type_combo.setCurrentText("Folder")
        self.output_folder_combo.setCurrentText(self.user_config.get('output_folder_option', DEFAULT_CONFIG['output_folder_option']))
        self.custom_output_path_edit.setText(self.user_config.get('custom_output_path', DEFAULT_CONFIG['custom_output_path']))
        self.update_output_custom_path_state()
        self.api_key_edit.setText(self.user_config.get('openai_api_key', DEFAULT_CONFIG['openai_api_key']))
        self.filename_lang_combo.setCurrentText(self.user_config.get('filename_language', DEFAULT_CONFIG['filename_language']))
        self.alttext_lang_combo.setCurrentText(self.user_config.get('alttext_language', DEFAULT_CONFIG['alttext_language']))
        self.name_detail_combo.setCurrentText(self.user_config.get('name_detail_level', DEFAULT_CONFIG['name_detail_level']))
        self.vision_detail_combo.setCurrentText(self.user_config.get('vision_detail', DEFAULT_CONFIG['vision_detail']))
        self.ai_model_combo.setCurrentText(self.user_config.get('ai_model', DEFAULT_CONFIG['ai_model']))
        self.ocr_enabled_checkbox.setChecked(self.user_config.get('ocr_enabled', DEFAULT_CONFIG['ocr_enabled']))
        self.tesseract_path_edit.setText(self.user_config.get('tesseract_path', DEFAULT_CONFIG['tesseract_path']))
        self.ocr_language_edit.setText(self.user_config.get('ocr_language', DEFAULT_CONFIG['ocr_language']))
        accumulated_tokens = self.user_config.get('total_accumulated_tokens', 0)
        self.total_tokens_label.setText(f"Total Accumulated Tokens: {accumulated_tokens}")
        self.session_tokens_label.setText("Session Tokens: 0")
        self.estimated_cost_label.setText("Estimated Session Cost: $0.0000")
        geom_str = self.user_config.get('window_geometry', DEFAULT_CONFIG['window_geometry'])
        try:
            width, height = map(int, geom_str.split('x'))
            self.resize(width, height)
        except ValueError:
            self.logger.warn(f"Invalid window geometry string in config: {geom_str}. Using default.")
            width, height = map(int, DEFAULT_CONFIG['window_geometry'].split('x'))
            self.resize(width, height)
        self.logger.info(f"Window resized to {self.width()}x{self.height()}")
        current_theme_name = self.user_config.get('ui_theme', DEFAULT_CONFIG['ui_theme'])
        self.theme_combo.setCurrentText(current_theme_name) 
        self.apply_theme(current_theme_name)

    def apply_theme(self, theme_name: str):
        file_name = f"{theme_name.lower().replace(' ', '')}.qss"
        file_path = os.path.join(self.themes_dir, file_name)
        try:
            with open(file_path, "r") as f:
                qss_content = f.read()
            QApplication.instance().setStyleSheet(qss_content)
            self.logger.info(f"Applied theme: {theme_name}")
        except FileNotFoundError:
            self.logger.warn(f"Theme file not found: {file_path}. Using default Qt style.")
            QApplication.instance().setStyleSheet("") 
        except Exception as e:
            self.logger.error(f"Error applying theme {theme_name}: {e}")
            QApplication.instance().setStyleSheet("")

    def save_current_settings(self, show_message=True):
        self.logger.info("Saving current settings...")
        config_to_save = {
            'custom_output_path': self.custom_output_path_edit.text(),
            'output_folder_option': self.output_folder_combo.currentText(),
            'openai_api_key': self.api_key_edit.text(), 
            'filename_language': self.filename_lang_combo.currentText(),
            'alttext_language': self.alttext_lang_combo.currentText(),
            'name_detail_level': self.name_detail_combo.currentText(),
            'vision_detail': self.vision_detail_combo.currentText(),
            'ai_model': self.ai_model_combo.currentText(),
            'ocr_enabled': self.ocr_enabled_checkbox.isChecked(),
            'tesseract_path': self.tesseract_path_edit.text(),
            'ocr_language': self.ocr_language_edit.text(),
            'ui_theme': self.theme_combo.currentText(),
            'ui_language': self.user_config.get('ui_language', DEFAULT_CONFIG['ui_language']),
            'global_images_count': self.user_config.get('global_images_count', 0),
            'total_accumulated_tokens': self.user_config.get('total_accumulated_tokens', 0),
        }
        window_geom_str = f"{self.width()}x{self.height()}"
        try:
            save_config(config_to_save, window_geom_str)
            self.logger.info("Settings saved successfully.")
            if show_message: 
                QMessageBox.information(self, "Settings Saved", "Settings saved successfully.")
            self.user_config = load_config() 
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            if show_message:
                QMessageBox.critical(self, "Save Error", f"Could not save settings: {e}")

    def start_image_processing(self):
        self.logger.info("Starting image processing...")
        self.session_tokens_label.setText("Session Tokens: 0")
        self.estimated_cost_label.setText("Estimated Session Cost: $0.0000")
        input_path = self.input_path_edit.text()
        if not input_path or not os.path.exists(input_path):
            QMessageBox.warning(self, "Input Error", "Please select a valid input path.")
            self.logger.error("Invalid input path provided for processing.")
            return
        state = {
            'input_type': self.input_type_combo.currentText(),
            'input_path': input_path,
            'custom_output_path': self.custom_output_path_edit.text(),
            'output_folder_option': self.output_folder_combo.currentText(),
            'openai_api_key': self.api_key_edit.text(),
            'filename_language': self.filename_lang_combo.currentText().lower(),
            'alttext_language': self.alttext_lang_combo.currentText().lower(),
            'name_detail_level': self.name_detail_combo.currentText().lower(),
            'vision_detail': self.vision_detail_combo.currentText().lower(),
            'ai_model': self.ai_model_combo.currentText(),
            'ocr_enabled': self.ocr_enabled_checkbox.isChecked(),
            'ui_language': 'English', 
            'tesseract_path': self.tesseract_path_edit.text(),
            'ocr_language': self.ocr_language_edit.text(),
            'ui_theme': self.theme_combo.currentText(),
            'total_tokens': 0, 
            'global_images_count': self.user_config.get('global_images_count', 0)
        }
        self.logger.debug(f"Processing state: {state}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) 
        self.process_button.setEnabled(False)
        
        # Setup and start the thread
        self.thread = QThread()
        self.worker = ProcessingWorker(self.logger, state)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_processing_finished)
        self.worker.error.connect(self.handle_processing_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.logger.info("Processing thread started.")

    def handle_processing_finished(self, summary_result):
        self.logger.info("Processing finished successfully.")
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if summary_result:
            tokens_this_run = summary_result.get('tokens_used_this_run', 0)
            self.session_tokens_label.setText(f"Session Tokens: {tokens_this_run}")
            cost = (tokens_this_run / 1000) * GPT_NANO_TOKEN_COST_PER_1K
            self.estimated_cost_label.setText(f"Estimated Session Cost: ${cost:.4f}")
            current_total_accumulated = self.user_config.get('total_accumulated_tokens', 0)
            new_total_accumulated = current_total_accumulated + tokens_this_run
            self.user_config['total_accumulated_tokens'] = new_total_accumulated
            self.total_tokens_label.setText(f"Total Accumulated Tokens: {new_total_accumulated}")
            updated_global_images = summary_result.get('updated_global_images_count', self.user_config.get('global_images_count', 0))
            self.user_config['global_images_count'] = updated_global_images
            self.save_current_settings(show_message=False)
            QMessageBox.information(self, "Processing Complete", summary_result.get("message", "Done!"))
        else:
            self.logger.warn("Processing finished but no summary result was received.")
            QMessageBox.warning(self, "Processing Issue", "Processing completed but returned no summary.")
        
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(1000)

    def handle_processing_error(self, error_message):
        self.logger.error(f"Handling processing error: {error_message}")
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Processing Error", f"An error occurred during processing:\n{error_message}")
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(1000)

    def reset_accumulated_tokens_count(self):
        reply = QMessageBox.question(self, "Reset Tokens", 
                                     "Are you sure you want to reset the total accumulated token count?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.user_config['total_accumulated_tokens'] = 0
            self.total_tokens_label.setText("Total Accumulated Tokens: 0")
            self.save_current_settings(show_message=False) 
            self.logger.info("Total accumulated token count has been reset.")
            QMessageBox.information(self, "Tokens Reset", "Total accumulated token count reset to 0.")
            
    def handle_open_config_folder(self):
        try:
            open_config_folder()
            self.logger.info("Opened config folder.")
        except Exception as e:
            self.logger.error(f"Could not open config folder: {e}")
            QMessageBox.warning(self, "Error", f"Could not open config folder: {e}")

    def handle_reset_defaults(self):
        reply = QMessageBox.question(self, "Reset Settings",
                                     "Are you sure you want to reset all settings to their default values?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                reset_config()
                self.user_config = load_config()
                self._populate_ui_from_config()
                self.logger.info("Application settings have been reset to defaults.")
                QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults.")
            except Exception as e:
                self.logger.error(f"Error resetting defaults: {e}")
                QMessageBox.critical(self, "Error", f"Could not reset settings: {e}")

    def show_about_dialog(self):
        QMessageBox.about(self, "About Altomatic",
                           "Altomatic v2.0 (PyQt6)\n\n"
                           "Originally created by Mehdi Bazyar.\n"
                           "This version re-implemented and enhanced by Jules (AI Agent).\n\n"
                           "Altomatic is a tool to analyze images and automatically "
                           "generate descriptive filenames and alt text using AI.")

    def append_log_message(self, message: str, level: str):
        color_map = {
            "info": QColor("blue"), "warn": QColor("orange"), "error": QColor("red"),
            "success": QColor("green"), "debug": QColor("purple"), "token": QColor("#009688"), 
            "default": self.log_display.textColor()
        }
        self.log_display.setTextColor(color_map.get(level.lower(), color_map["default"]))
        self.log_display.append(f"[{level.upper()}] {message.strip()}")

    def browse_tesseract_path(self):
        executable_filter = "All Files (*)"
        if sys.platform == "win32": executable_filter = "Executables (*.exe);;All Files (*)"
        elif sys.platform == "darwin": executable_filter = "Applications (*.app);;All Files (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Tesseract Executable", "", executable_filter)
        if path: self.tesseract_path_edit.setText(path)

    def update_output_custom_path_state(self):
        is_custom = self.output_folder_combo.currentText() == "Custom"
        self.custom_output_path_edit.setEnabled(is_custom)
        self.browse_output_button.setEnabled(is_custom)
        if not is_custom: self.custom_output_path_edit.clear()

    def browse_custom_output_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Custom Output Folder")
        if path: self.custom_output_path_edit.setText(path)

    def update_image_count(self):
        path = self.input_path_edit.text()
        input_type = self.input_type_combo.currentText()
        count = 0; status_message = ""
        if not path: 
            status_message = "0 image(s) selected"
            self.image_preview_label.clear()
            self.image_preview_label.setText("Image Preview")
        elif os.path.isdir(path) and input_type == "Folder":
            try:
                image_files = [f for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                count = len(image_files)
                status_message = f"{count} image(s) selected."
                self.image_preview_label.clear()
                self.image_preview_label.setText("Preview: Folder selected")
                if count > 0:
                    first_image_path = os.path.join(path, image_files[0])
                    if first_image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                        pixmap = QPixmap(first_image_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(
                                self.image_preview_label.size(), 
                                Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation
                            )
                            self.image_preview_label.setPixmap(scaled_pixmap)
                        else:
                            self.image_preview_label.setText("Preview: Folder (1st img invalid)") 
            except OSError: 
                status_message = "Error reading directory."
                self.image_preview_label.clear()
                self.image_preview_label.setText("Image Preview")
        elif os.path.isfile(path) and input_type == "File":
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                count = 1
                status_message = "1 image selected."
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.image_preview_label.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_preview_label.setPixmap(scaled_pixmap)
                else:
                    self.image_preview_label.clear()
                    self.image_preview_label.setText("Preview: Not a valid image")
            else: 
                status_message = "Invalid file type."
                self.image_preview_label.clear()
                self.image_preview_label.setText("Preview: Not an image file")
        elif input_type == "Folder": 
            status_message = "Path is not a valid directory."
            self.image_preview_label.clear()
            self.image_preview_label.setText("Image Preview")
        elif input_type == "File": 
            status_message = "Path is not a valid file."
            self.image_preview_label.clear()
            self.image_preview_label.setText("Image Preview")
        else: 
            status_message = "Invalid path or type."
            self.image_preview_label.clear()
            self.image_preview_label.setText("Image Preview")
            
        self.image_count_label.setText(status_message)

    def browse_input_path(self):
        current_type = self.input_type_combo.currentText()
        path = ""
        if current_type == "Folder": path = QFileDialog.getExistingDirectory(self, "Select Folder")
        elif current_type == "File": path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Image Files (*.png *.jpg *.jpeg *.webp)")
        if path: self.input_path_edit.setText(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction); event.acceptProposedAction()
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    self.input_type_combo.setCurrentText("Folder"); self.input_path_edit.setText(path)
                elif os.path.isfile(path):
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        self.input_type_combo.setCurrentText("File"); self.input_path_edit.setText(path)
                    else: self.image_count_label.setText("Unsupported file type dropped.")
                else: self.image_count_label.setText("Dropped item is not a file or folder.")
        else: super().dropEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
