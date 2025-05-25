import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QTabWidget,
    QScrollArea, QFormLayout, QCheckBox, QGroupBox,
    QTextEdit, QDockWidget, QFileDialog, QProgressBar, QStatusBar,
    QDialog, QDialogButtonBox, QSizePolicy # Added for EditableResultsDialog
)
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap # For image preview
import helpers # For helpers.py integration
import os # For path operations in _update_image_count
import shutil # For file operations in worker / temp dir cleanup
import json # For API response parsing in worker (though ai_handler does this)
from datetime import datetime # For session folder/file names
import tempfile # For drag & drop of multiple files
# Import ai_handler to access describe_image_local
import ai_handler
# Import config module
import config
from PyQt6.QtWidgets import QMessageBox # For reset confirmation

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dropped_files_temp_dir = None # For drag & drop temp folder

        self.setWindowTitle("Altomatic PyQt")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # Create Tab Widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create Input Tab
        self.input_tab = QWidget()
        self.tabs.addTab(self.input_tab, "Input")
        self._create_input_tab_ui()

        # Create Output Tab
        self.output_tab = QWidget()
        self.tabs.addTab(self.output_tab, "Output")
        self._create_output_tab_ui()

        # Create Settings Tab
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Settings")
        self._create_settings_tab_ui()

        self._create_log_viewer_dock()
        self._setup_status_bar()

        # Connect signals
        self.browse_button.clicked.connect(self._browse_input_path)
        self.input_type_combo.currentTextChanged.connect(self._on_input_type_changed)
        self.custom_folder_browse_button.clicked.connect(self._browse_output_path)
        self.describe_button.clicked.connect(self._start_processing)

        # Connect Settings tab buttons
        self.save_settings_button.clicked.connect(self._save_settings)
        self.reset_defaults_button.clicked.connect(self._reset_settings)
        self.open_config_folder_button.clicked.connect(self._open_config_folder)
        self.reset_token_button.clicked.connect(self._reset_session_token_usage)
        self.reset_stats_button.clicked.connect(self._reset_global_stats)
        
        self._load_settings() # Load settings at the end of __init__


    def _setup_status_bar(self):
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100) # Default range, can be 0-0 for indeterminate
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False) # Initially hidden
        self.statusBar.addPermanentWidget(self.progress_bar)

    def _browse_input_path(self):
        input_type = self.input_type_combo.currentText()
        path = ""
        if input_type == "Folder":
            path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        elif input_type == "File":
            filters = "Image files (*.png *.jpg *.jpeg *.webp);;All files (*)"
            path, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", filters)
        
        if path:
            self.input_path_lineedit.setText(path)
            self._update_image_count(path, input_type)
        else:
            self.input_path_lineedit.setText("")
            self._update_image_count("", input_type)


    def _update_image_count(self, path, input_type):
        if hasattr(self, 'image_preview_label'): 
            self.image_preview_label.clear()
            self.image_preview_label.setText("Image Preview") 
            self.image_preview_label.hide()

        count = 0
        if path: 
            if input_type == "File":
                if os.path.isfile(path): 
                    count = 1
                    if hasattr(self, 'image_preview_label'):
                        try:
                            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                                pixmap = QPixmap(path)
                                if not pixmap.isNull():
                                    scaled_pixmap = pixmap.scaled(
                                        self.image_preview_label.width(),
                                        self.image_preview_label.height(),
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation
                                    )
                                    self.image_preview_label.setPixmap(scaled_pixmap)
                                    self.image_preview_label.show()
                                else:
                                    self.image_preview_label.setText("Cannot preview image.")
                                    self.image_preview_label.show()
                            else: 
                                self.image_preview_label.setText("No preview available\n(unsupported format).")
                                self.image_preview_label.show()
                        except Exception as e:
                            self.log_message(f"Error loading image preview: {e}", "ERROR")
                            self.image_preview_label.setText("Preview error.")
                            self.image_preview_label.show()
                else:
                    self.log_message(f"Selected file path does not exist: {path}", "ERROR")
                    self.input_path_lineedit.setText("") 
            elif input_type == "Folder":
                if os.path.isdir(path): 
                    try:
                        count = helpers.get_image_count_in_folder(path)
                    except Exception as e: 
                        self.log_message(f"Error counting images in folder {path}: {e}", "ERROR")
                        count = 0
                        self.input_path_lineedit.setText("") 
                else:
                    self.log_message(f"Selected folder path does not exist: {path}", "ERROR")
                    self.input_path_lineedit.setText("") 
        
        self.image_count_label.setText(f"Image Count: {count}")
        if count == 0 and path: 
             self.log_message(f"No supported images found in {path}", "WARNING")
        elif count > 0:
            self.log_message(f"Selected {input_type.lower()} with {count} image(s): {path}", "INFO")


    def _on_input_type_changed(self, text):
        self.log_message(f"Input type changed to: {text}", "INFO")
        self.input_path_lineedit.setText("")
        if hasattr(self, 'image_preview_label'): 
            if text == "Folder":
                self.image_preview_label.clear()
                self.image_preview_label.setText("Image Preview")
                self.image_preview_label.hide()
        self._update_image_count("", text) 

    def _browse_output_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Custom Output Folder")
        if path:
            self.custom_folder_lineedit.setText(path)
            self.log_message(f"Custom output folder set to: {path}", "INFO")

    def _start_processing(self):
        self.log_message("--- Processing started ---", "INFO")
        input_path = self.input_path_lineedit.text()
        api_key = self.api_key_lineedit.text() 
        input_type = self.input_type_combo.currentText()
        image_count_text = self.image_count_label.text() 
        image_count = int(image_count_text.split(":")[1].strip()) if ":" in image_count_text else 0

        if not input_path:
            self.log_message("Input path is not set. Please select a file or folder.", "ERROR")
            self.statusBar.showMessage("Error: Input path is required.", 5000) 
            return
        if image_count == 0:
            self.log_message("No images selected for processing.", "WARNING")
            self.statusBar.showMessage("Warning: No images to process.", 5000)
            return
        if not api_key:
            self.log_message("OpenAI API Key is not set in Settings.", "ERROR")
            self.statusBar.showMessage("Error: OpenAI API Key is required.", 5000)
            return
        
        self.log_message(f"Input Type: {input_type}", "DEBUG")
        self.log_message(f"Input Path: {input_path}", "DEBUG")
        self.log_message(f"API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '****'}", "DEBUG") 
        self.log_message(f"Total images to process: {image_count}", "INFO")

        if self.processing_thread and self.processing_thread.isRunning():
            self.log_message("Processing is already in progress.", "WARNING")
            self.statusBar.showMessage("Warning: Processing is already running.", 3000)
            return

        self.describe_button.setEnabled(False)
        self.cancel_button.show() # Show cancel button
        self.cancel_button.setEnabled(True) # Ensure it's enabled
        self.cancel_button.clicked.connect(self._request_cancel_processing)

        self.statusBar.showMessage("Processing...", 0) 
        self.progress_bar.setRange(0, image_count if image_count > 0 else 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        parameters = {
            'api_key': api_key, 'input_path': input_path, 'input_type': input_type,
            'output_folder_option': self.save_to_combo.currentText(),
            'custom_output_path': self.custom_folder_lineedit.text(),
            'filename_language': self.filename_lang_combo.currentText(),
            'alttext_language': self.alt_text_lang_combo.currentText(),
            'name_detail_level': self.name_detail_combo.currentText(),
            'vision_detail': self.vision_detail_combo.currentText(),
            'ocr_enabled': self.enable_ocr_checkbox.isChecked(),
            'tesseract_path': self.tesseract_path_lineedit.text(),
            'ocr_lang': self.ocr_lang_lineedit.text()
        }

        self.processing_thread = QThread()
        self.worker = ProcessingWorker(parameters)
        self.worker.moveToThread(self.processing_thread)

        self.worker.progress_updated.connect(self.update_progress_bar_slot)
        self.worker.log_message_signal.connect(self.log_message_slot) 
        self.worker.ai_processing_complete.connect(self._start_review_phase)
        self.worker.processing_cancelled.connect(self._handle_processing_cancelled) # Connect new signal
        self.worker.error_occurred.connect(self.processing_error_slot)
        
        self.processing_thread.started.connect(self.worker.run)
        
        self.worker.ai_processing_complete.connect(self.processing_thread.quit) 
        self.worker.processing_cancelled.connect(self.processing_thread.quit) 
        self.worker.error_occurred.connect(self.processing_thread.quit) 
        self.processing_thread.finished.connect(self.worker.deleteLater)
        self.processing_thread.finished.connect(self.processing_thread.deleteLater)
        
        self.processing_thread.start()
        self.log_message("Worker thread started for processing.", "DEBUG")

    def _request_cancel_processing(self):
        if hasattr(self, 'worker') and self.worker:
            self.worker.request_cancel()
            self.log_message("Requesting cancellation of AI processing...", "INFO")
            self.cancel_button.setEnabled(False) 

    def _handle_processing_cancelled(self, message):
        self.log_message(message, "WARNING") 
        self.statusBar.showMessage(message, 5000)
        self.describe_button.setEnabled(True)
        self.cancel_button.hide()
        self.cancel_button.setEnabled(True) 
        self.progress_bar.setVisible(False) 

        if self.processing_thread and self.processing_thread.isRunning():
            self.log_message("Quitting worker thread due to cancellation.", "DEBUG")
            self.processing_thread.quit()

        if hasattr(self, 'dropped_files_temp_dir') and self.dropped_files_temp_dir:
            try:
                shutil.rmtree(self.dropped_files_temp_dir)
                self.log_message(f"Temporary input folder {self.dropped_files_temp_dir} cleaned up on cancellation.", "INFO")
            except Exception as e:
                self.log_message(f"Error cleaning up temporary folder {self.dropped_files_temp_dir} on cancellation: {e}", "ERROR")
            finally:
                self.dropped_files_temp_dir = None

    def update_progress_bar_slot(self, value):
        self.progress_bar.setValue(value)

    def log_message_slot(self, message, level): 
        self.log_message(message, level)

    def processing_finished_slot(self, summary_message, total_tokens_used_session):
        self.log_message(summary_message, "INFO")
        self.statusBar.showMessage("Processing finished.", 5000) 
        self.progress_bar.setVisible(False)
        self.describe_button.setEnabled(True)
        self.cancel_button.hide() # Ensure cancel button is hidden
        self.cancel_button.setEnabled(True) # Re-enable for next run
        
        current_overall_tokens = 0
        try:
            parts = self.token_usage_label.text().split(":")
            if len(parts) > 1:
                current_overall_tokens = int(parts[1].strip())
        except ValueError:
            self.log_message("Could not parse current overall token count.", "WARNING")
            current_overall_tokens = 0 

        self.token_usage_label.setText(f"Tokens used (this session): {total_tokens_used_session}")
        self.log_message(f"Session token display updated: {total_tokens_used_session}", "DEBUG")
        
        if hasattr(self, 'dropped_files_temp_dir') and self.dropped_files_temp_dir:
            try:
                shutil.rmtree(self.dropped_files_temp_dir)
                self.log_message(f"Temporary input folder {self.dropped_files_temp_dir} cleaned up.", "INFO")
            except Exception as e:
                self.log_message(f"Error cleaning up temporary folder {self.dropped_files_temp_dir}: {e}", "ERROR")
            finally:
                self.dropped_files_temp_dir = None

    def processing_error_slot(self, error_message):
        self.log_message(f"Processing Error: {error_message}", "ERROR")
        self.statusBar.showMessage(f"Error: {error_message}", 5000) 
        self.progress_bar.setVisible(False)
        self.describe_button.setEnabled(True) 
        self.cancel_button.hide() 
        self.cancel_button.setEnabled(True)

        if hasattr(self, 'dropped_files_temp_dir') and self.dropped_files_temp_dir:
            try:
                shutil.rmtree(self.dropped_files_temp_dir)
                self.log_message(f"Temporary input folder {self.dropped_files_temp_dir} cleaned up on error.", "INFO")
            except Exception as e:
                self.log_message(f"Error cleaning up temporary folder {self.dropped_files_temp_dir} on error: {e}", "ERROR")
            finally:
                self.dropped_files_temp_dir = None
    
    def _start_review_phase(self, ai_results_list, session_path, renamed_folder_path, summary_txt_path, session_total_tokens):
        self.cancel_button.hide() # Worker phase done, hide cancel button
        self.cancel_button.setEnabled(True) # Re-enable for next time
        self.log_message(f"AI processing complete. Starting review phase for {len(ai_results_list)} items.", "INFO")
        self.log_message(f"Session Path: {session_path}", "DEBUG")
        self.log_message(f"Renamed Folder Target: {renamed_folder_path}", "DEBUG")
        self.log_message(f"Summary File Target: {summary_txt_path}", "DEBUG")
        self.log_message(f"Total tokens from AI phase: {session_total_tokens}", "TOKEN")

        self.current_review_data = {
            "ai_results_list": ai_results_list, 
            "session_path": session_path,
            "renamed_folder_path": renamed_folder_path,
            "summary_txt_path": summary_txt_path,
            "session_total_tokens": session_total_tokens,
        }
        
        self.final_edited_results = [] 
        self.current_review_index = 0  

        self.describe_button.setEnabled(False) 
        self.statusBar.showMessage("Reviewing AI results...", 0) 
        self.progress_bar.setRange(0, len(ai_results_list)) 
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        self._show_next_review_dialog()


    def _show_next_review_dialog(self):
        ai_results_list = self.current_review_data['ai_results_list']

        if self.current_review_index < len(ai_results_list):
            item_data = ai_results_list[self.current_review_index]
            original_path = item_data['original_path']
            proposed_slug = item_data['slugified_name']
            proposed_alt = item_data['raw_ai_alt']
            item_extension = item_data['extension']
            had_error = item_data.get('error') 

            self.progress_bar.setValue(self.current_review_index + 1)

            if had_error:
                self.log_message(f"Skipping review for {os.path.basename(original_path)} due to earlier AI processing error: {had_error}", "WARNING")
                self.final_edited_results.append({
                    'original_path': original_path, 
                    'edited_name': proposed_slug, 
                    'edited_alt': proposed_alt if proposed_alt else "AI processing failed.", 
                    'extension': item_extension, 
                    'had_error': True
                })
            else:
                dialog = EditableResultsDialog(os.path.basename(original_path), proposed_slug, proposed_alt, self)
                if dialog.exec(): 
                    edited_data = dialog.get_edited_data()
                    self.final_edited_results.append({
                        'original_path': original_path, 
                        'edited_name': edited_data['name'], 
                        'edited_alt': edited_data['alt'], 
                        'extension': item_extension,
                        'had_error': False
                    })
                    self.log_message(f"Accepted edits for {os.path.basename(original_path)}", "INFO")
                else: 
                    self.log_message(f"Review cancelled for {os.path.basename(original_path)}. Using original AI results.", "INFO")
                    self.final_edited_results.append({
                        'original_path': original_path, 
                        'edited_name': proposed_slug, 
                        'edited_alt': proposed_alt,   
                        'extension': item_extension,
                        'had_error': False 
                    })

            self.current_review_index += 1
            self._show_next_review_dialog() 
        else: 
            self.log_message("Review complete. Finalizing file writing...", "INFO")
            self.progress_bar.setVisible(False) 
            self.statusBar.showMessage("Finalizing files...", 0)

            self._finalize_file_writing(
                self.current_review_data['session_path'],
                self.current_review_data['renamed_folder_path'],
                self.current_review_data['summary_txt_path'],
                self.current_review_data['session_total_tokens']
            )

    def _finalize_file_writing(self, session_path, renamed_folder_path, summary_txt_path, total_tokens):
        self.log_message(f"Starting file finalization. Target folder: {renamed_folder_path}", "DEBUG")
        try:
            os.makedirs(renamed_folder_path, exist_ok=True)
        except Exception as e:
            self.processing_error_slot(f"Could not create renamed images folder '{renamed_folder_path}': {e}")
            return 

        num_successfully_written = 0
        num_ai_errors_skipped_write = 0
        
        try:
            with open(summary_txt_path, "w", encoding="utf-8") as txt_f:
                for idx, item in enumerate(self.final_edited_results):
                    self.statusBar.showMessage(f"Writing file {idx+1}/{len(self.final_edited_results)}...", 0)
                    if item['had_error']:
                        num_ai_errors_skipped_write += 1
                        txt_f.write(f"[Original: {os.path.basename(item['original_path'])}]\n")
                        txt_f.write(f"Error: AI processing failed. See failed.log.\n\n")
                        continue 

                    original_file_path = item['original_path']
                    base_output_name = helpers.slugify(item['edited_name'])[:100] 
                    if not base_output_name: 
                        base_output_name = f"image-{idx+1}" 
                    
                    file_ext = item['extension']

                    output_filename_base_for_uniqueness = base_output_name
                    current_output_filename = f"{base_output_name}{file_ext}"
                    output_file_path = os.path.join(renamed_folder_path, current_output_filename)
                    counter = 1
                    while os.path.exists(output_file_path):
                        current_output_filename = f"{output_filename_base_for_uniqueness}_{counter}{file_ext}"
                        output_file_path = os.path.join(renamed_folder_path, current_output_filename)
                        counter += 1
                    
                    try:
                        shutil.copy(original_file_path, output_file_path)
                        final_written_basename = os.path.splitext(current_output_filename)[0]
                        txt_f.write(f"[Original: {os.path.basename(original_file_path)}]\n")
                        txt_f.write(f"Name: {final_written_basename}\n")
                        txt_f.write(f"Alt: {item['edited_alt']}\n\n")
                        num_successfully_written += 1
                    except Exception as copy_e:
                        self.log_message(f"Error copying file {original_file_path} to {output_file_path}: {copy_e}", "ERROR")
                        txt_f.write(f"[Original: {os.path.basename(original_file_path)}]\n")
                        txt_f.write(f"Error: Failed to copy file during finalization: {copy_e}\n\n")

            summary_msg = (f"✅ Processed and saved {num_successfully_written} image(s).\n"
                           f"{num_ai_errors_skipped_write} image(s) had AI processing errors (details in failed.log).\n"
                           f"Session folder: {session_path}\n"
                           f"Output file: {os.path.basename(summary_txt_path)}\n\n"
                           f"Token usage this run: {total_tokens}")
            
            self.log_message(summary_msg, "SUCCESS")
            self.processing_finished_slot(summary_msg, total_tokens)

        except Exception as e:
            error_final_msg = f"Error during final file writing: {e}"
            self.log_message(error_final_msg, "ERROR")
            self.processing_error_slot(error_final_msg) 
        finally:
            self.current_review_data = None 
            self.final_edited_results = []
            self.current_review_index = 0
            self.describe_button.setEnabled(True)
            self.progress_bar.setVisible(False) 
            self.cancel_button.hide() 
            self.cancel_button.setEnabled(True) 


    def _create_log_viewer_dock(self):
        self.log_dock_widget = QDockWidget("Logs", self)
        self.log_dock_widget.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea) 

        dock_content_widget = QWidget()
        dock_layout = QVBoxLayout(dock_content_widget)

        log_buttons_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("Clear Log")
        self.copy_log_button = QPushButton("Copy Log")
        log_buttons_layout.addWidget(self.clear_log_button)
        log_buttons_layout.addWidget(self.copy_log_button)
        log_buttons_layout.addStretch() 

        dock_layout.addLayout(log_buttons_layout)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        dock_layout.addWidget(self.log_text_edit) 

        dock_content_widget.setLayout(dock_layout)
        self.log_dock_widget.setWidget(dock_content_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock_widget)
        
        self.log_message("Application started. Log viewer initialized.", "INFO")

        self.processing_thread = None 
        self.worker = None            

    # --- Configuration Methods ---
    def _load_settings(self):
        self.log_message("Loading configuration...", "DEBUG")
        config_data = config.load_config()

        self.save_to_combo.setCurrentText(config_data.get('output_folder_option', config.DEFAULT_CONFIG['output_folder_option']))
        self.custom_folder_lineedit.setText(config_data.get('custom_output_path', config.DEFAULT_CONFIG['custom_output_path']))

        self.api_key_lineedit.setText(config_data.get('openai_api_key', config.DEFAULT_CONFIG['openai_api_key']))
        self.ui_theme_combo.setCurrentText(config_data.get('ui_theme', config.DEFAULT_CONFIG['ui_theme']))
        self.filename_lang_combo.setCurrentText(config_data.get('filename_language', config.DEFAULT_CONFIG['filename_language']))
        self.alt_text_lang_combo.setCurrentText(config_data.get('alttext_language', config.DEFAULT_CONFIG['alttext_language']))
        self.name_detail_combo.setCurrentText(config_data.get('name_detail_level', config.DEFAULT_CONFIG['name_detail_level']))
        self.vision_detail_combo.setCurrentText(config_data.get('vision_detail', config.DEFAULT_CONFIG['vision_detail']))
        
        self.enable_ocr_checkbox.setChecked(config_data.get('ocr_enabled', config.DEFAULT_CONFIG['ocr_enabled']))
        self.tesseract_path_lineedit.setText(config_data.get('tesseract_path', config.DEFAULT_CONFIG['tesseract_path']))
        self.ocr_lang_lineedit.setText(config_data.get('ocr_language', config.DEFAULT_CONFIG['ocr_language']))

        geom_str = config_data.get('window_geometry', config.DEFAULT_CONFIG['window_geometry'])
        try:
            width, height = map(int, geom_str.split('x'))
            self.resize(width, height)
            self.log_message(f"Window resized to {width}x{height} from config.", "DEBUG")
        except ValueError:
            self.log_message(f"Invalid window geometry string in config: {geom_str}. Using default.", "WARNING")
            width, height = map(int, config.DEFAULT_CONFIG['window_geometry'].split('x'))
            self.resize(width, height)
        
        self.log_message("Configuration loaded.", "INFO")


    def _save_settings(self):
        self.log_message("Saving configuration...", "INFO")
        settings_to_save = {
            'output_folder_option': self.save_to_combo.currentText(),
            'custom_output_path': self.custom_folder_lineedit.text(),
            'openai_api_key': self.api_key_lineedit.text(),
            'ui_theme': self.ui_theme_combo.currentText(),
            'filename_language': self.filename_lang_combo.currentText(),
            'alttext_language': self.alt_text_lang_combo.currentText(),
            'name_detail_level': self.name_detail_combo.currentText(),
            'vision_detail': self.vision_detail_combo.currentText(),
            'ocr_enabled': self.enable_ocr_checkbox.isChecked(),
            'tesseract_path': self.tesseract_path_lineedit.text(),
            'ocr_language': self.ocr_lang_lineedit.text(),
            'ui_language': config.load_config().get('ui_language', config.DEFAULT_CONFIG['ui_language'])
        }
        
        geom_str = f"{self.size().width()}x{self.size().height()}"
        config.save_config(settings_to_save, geom_str)
        self.log_message("Settings saved.", "SUCCESS")
        self.statusBar.showMessage("Settings saved successfully.", 3000)

    def _reset_settings(self):
        reply = QMessageBox.question(self, "Reset Settings",
                                     "Are you sure you want to reset all settings to their default values?\n"
                                     "The application will load defaults, but a restart might be needed for some changes.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.log_message("Resetting configuration to defaults...", "INFO")
            config.reset_config()
            self._load_settings() 
            self.log_message("Settings have been reset to defaults. A restart may be recommended for all changes to take effect.", "SUCCESS")
            self.statusBar.showMessage("Settings reset to defaults.", 3000)
        else:
            self.log_message("Settings reset cancelled by user.", "INFO")

    def _open_config_folder(self):
        self.log_message("Opening config folder...", "INFO")
        try:
            config.open_config_folder()
        except Exception as e:
            self.log_message(f"Could not open config folder: {e}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not open config folder: {e}")

    def _reset_session_token_usage(self):
        self.token_usage_label.setText("Tokens used (this session): 0")
        self.log_message("Session token usage display reset.", "INFO")
        self.statusBar.showMessage("Session token display reset.", 3000)
        
    def _reset_global_stats(self):
        self.log_message("Global stats reset functionality is not fully implemented yet. Only session stats are currently tracked.", "INFO")
        QMessageBox.information(self, "Global Stats", "Global stats reset functionality is not fully implemented yet.\nOnly session token usage is currently tracked and can be reset via its own button.")


    def _create_input_tab_ui(self):
        input_tab_layout = QVBoxLayout()
        self.input_tab.setLayout(input_tab_layout)

        input_type_layout = QHBoxLayout()
        input_type_label = QLabel("Input Type:")
        self.input_type_combo = QComboBox()
        self.input_type_combo.addItems(["Folder", "File"])
        input_type_layout.addWidget(input_type_label)
        input_type_layout.addWidget(self.input_type_combo)
        input_type_layout.addStretch() 
        input_tab_layout.addLayout(input_type_layout)

        input_path_layout = QHBoxLayout()
        input_path_label = QLabel("Input Path:")
        self.input_path_lineedit = QLineEdit()
        self.input_path_lineedit.setDragEnabled(True) 
        self.input_path_lineedit.setAcceptDrops(True)  
        self.input_path_lineedit.installEventFilter(self) 
        self.browse_button = QPushButton("Browse...")
        input_path_layout.addWidget(input_path_label)
        input_path_layout.addWidget(self.input_path_lineedit)
        input_path_layout.addWidget(self.browse_button)
        input_tab_layout.addLayout(input_path_layout)

        describe_button_layout = QHBoxLayout()
        self.describe_button = QPushButton("Describe Images")
        self.cancel_button = QPushButton("Cancel") 
        self.cancel_button.hide() 

        describe_button_layout.addStretch()
        describe_button_layout.addWidget(self.describe_button)
        describe_button_layout.addWidget(self.cancel_button) 
        describe_button_layout.addStretch()
        input_tab_layout.addLayout(describe_button_layout)

        input_tab_layout.addStretch()

        self.image_count_label = QLabel("Image Count: 0")
        self.image_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        input_tab_layout.addWidget(self.image_count_label)

        self.image_preview_label = QLabel("Image Preview")
        self.image_preview_label.setFixedSize(250, 250)
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setStyleSheet("border: 1px solid gray; color: gray;") 
        self.image_preview_label.hide() 
        input_tab_layout.addWidget(self.image_preview_label, alignment=Qt.AlignmentFlag.AlignCenter)


    def _create_output_tab_ui(self):
        output_tab_layout = QVBoxLayout()
        self.output_tab.setLayout(output_tab_layout)

        save_to_layout = QHBoxLayout()
        save_to_label = QLabel("Save to:")
        self.save_to_combo = QComboBox()
        self.save_to_combo.addItems(["Same as input", "Pictures", "Desktop", "Custom"])
        save_to_layout.addWidget(save_to_label)
        save_to_layout.addWidget(self.save_to_combo)
        save_to_layout.addStretch() 
        output_tab_layout.addLayout(save_to_layout)

        custom_folder_layout = QHBoxLayout()
        custom_folder_label = QLabel("Custom Folder:")
        self.custom_folder_lineedit = QLineEdit()
        self.custom_folder_browse_button = QPushButton("Browse...")
        custom_folder_layout.addWidget(custom_folder_label)
        custom_folder_layout.addWidget(self.custom_folder_lineedit)
        custom_folder_layout.addWidget(self.custom_folder_browse_button)
        output_tab_layout.addLayout(custom_folder_layout)

        output_tab_layout.addStretch()

        self.token_usage_label = QLabel("Tokens used: 0")
        self.token_usage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        output_tab_layout.addWidget(self.token_usage_label)

    def _create_settings_tab_ui(self):
        scroll_content_widget = QWidget()
        settings_main_layout = QVBoxLayout(scroll_content_widget)
        settings_main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content_widget)
        
        settings_tab_wrapper_layout = QVBoxLayout(self.settings_tab)
        settings_tab_wrapper_layout.addWidget(scroll_area)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows) 

        self.api_key_lineedit = QLineEdit()
        self.api_key_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("OpenAI API Key:", self.api_key_lineedit)

        self.ui_theme_combo = QComboBox()
        self.ui_theme_combo.addItems(["Light", "Dark", "BlueGray", "Solarized", "Pinky"])
        form_layout.addRow("UI Theme:", self.ui_theme_combo)

        self.filename_lang_combo = QComboBox()
        self.filename_lang_combo.addItems(["English", "Persian"])
        form_layout.addRow("Filename Language:", self.filename_lang_combo)

        self.alt_text_lang_combo = QComboBox()
        self.alt_text_lang_combo.addItems(["English", "Persian"])
        form_layout.addRow("Alt Text Language:", self.alt_text_lang_combo)

        self.name_detail_combo = QComboBox()
        self.name_detail_combo.addItems(["Minimal", "Normal", "Detailed"])
        form_layout.addRow("Name Detail Level:", self.name_detail_combo)

        self.vision_detail_combo = QComboBox()
        self.vision_detail_combo.addItems(["low", "high", "auto"])
        form_layout.addRow("Image Vision Detail:", self.vision_detail_combo)
        
        settings_main_layout.addLayout(form_layout)

        ocr_groupbox = QGroupBox("OCR Settings")
        ocr_layout = QVBoxLayout()

        self.enable_ocr_checkbox = QCheckBox("Enable OCR")
        ocr_layout.addWidget(self.enable_ocr_checkbox)

        tesseract_path_layout = QHBoxLayout()
        tesseract_path_label = QLabel("Tesseract Path:")
        self.tesseract_path_lineedit = QLineEdit()
        self.tesseract_browse_button = QPushButton("Browse...")
        tesseract_path_layout.addWidget(tesseract_path_label)
        tesseract_path_layout.addWidget(self.tesseract_path_lineedit)
        tesseract_path_layout.addWidget(self.tesseract_browse_button)
        ocr_layout.addLayout(tesseract_path_layout)

        ocr_lang_layout = QHBoxLayout()
        ocr_lang_label = QLabel("OCR Language:")
        self.ocr_lang_lineedit = QLineEdit()
        self.ocr_lang_lineedit.setFixedWidth(50)
        ocr_lang_layout.addWidget(ocr_lang_label)
        ocr_lang_layout.addWidget(self.ocr_lang_lineedit)
        ocr_lang_layout.addStretch() 
        ocr_layout.addLayout(ocr_lang_layout)
        
        ocr_groupbox.setLayout(ocr_layout)
        settings_main_layout.addWidget(ocr_groupbox)

        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight) 

        self.save_settings_button = QPushButton("Save Settings")
        self.reset_defaults_button = QPushButton("Reset Defaults")
        self.open_config_folder_button = QPushButton("Open Config Folder")
        self.reset_token_button = QPushButton("Reset Token Usage")
        self.reset_stats_button = QPushButton("Reset Analyzed Stats")

        action_buttons_layout.addWidget(self.save_settings_button)
        action_buttons_layout.addWidget(self.reset_defaults_button)
        action_buttons_layout.addWidget(self.open_config_folder_button)
        action_buttons_layout.addWidget(self.reset_token_button)
        action_buttons_layout.addWidget(self.reset_stats_button)
        
        settings_main_layout.addStretch() 
        settings_main_layout.addLayout(action_buttons_layout)

    LEVEL_COLORS = {
        "INFO": "blue", "ERROR": "red", "WARNING": "orange", 
        "SUCCESS": "green", "TOKEN": "#009688", "DEBUG": "purple"
    }

    def log_message(self, message: str, level: str = "INFO"):
        level_upper = level.upper() 
        color = self.LEVEL_COLORS.get(level_upper, "black")
        escaped_message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_message = f'<font color="{color}"><b>{level_upper}:</b> {escaped_message}</font>'
        self.log_text_edit.append(html_message)
        self.log_text_edit.ensureCursorVisible()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


# --- Editable Results Dialog ---
# QDialog, QDialogButtonBox, QSizePolicy already imported at the top

class EditableResultsDialog(QDialog):
    def __init__(self, original_filename, proposed_name, proposed_alt, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit AI Results")
        self.original_filename = original_filename 
        layout = QVBoxLayout(self)
        self.info_label = QLabel(f"<b>Original:</b> {os.path.basename(original_filename)}")
        self.info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse) 
        layout.addWidget(self.info_label)
        self.name_label = QLabel("Proposed Filename (no extension):")
        layout.addWidget(self.name_label)
        self.name_edit = QLineEdit(proposed_name)
        layout.addWidget(self.name_edit)
        self.alt_label = QLabel("Proposed Alt Text:")
        layout.addWidget(self.alt_label)
        self.alt_edit = QTextEdit(proposed_alt)
        self.alt_edit.setMinimumHeight(100) 
        self.alt_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        layout.addWidget(self.alt_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        self.setMinimumWidth(450) 
        self.setMinimumHeight(300) 

    def get_edited_data(self) -> dict | None:
        if self.result() == QDialog.DialogCode.Accepted:
            return {'name': self.name_edit.text(), 'alt': self.alt_edit.toPlainText()}
        return None


class ProcessingWorker(QObject):
    progress_updated = pyqtSignal(int) 
    log_message_signal = pyqtSignal(str, str) 
    ai_processing_complete = pyqtSignal(list, str, str, str, int) 
    processing_finished = pyqtSignal(str, int) 
    processing_cancelled = pyqtSignal(str) # New signal
    error_occurred = pyqtSignal(str) 

    def __init__(self, parameters):
        super().__init__()
        self.parameters = parameters
        self._is_cancel_requested = False # Initialize cancel flag

    def request_cancel(self):
        self._is_cancel_requested = True
        if hasattr(self, 'log_message_signal'): 
            self.log_message_signal.emit("Worker received cancel request.", "DEBUG")

    def run(self):
        self.log_message_signal.emit("Worker thread started.", "DEBUG")
        images_to_process = []
        if self.parameters['input_type'] == "File":
            if os.path.isfile(self.parameters['input_path']):
                images_to_process = [self.parameters['input_path']]
            else:
                self.error_occurred.emit(f"Input file does not exist: {self.parameters['input_path']}")
                return
        else: 
            if os.path.isdir(self.parameters['input_path']):
                images_to_process = helpers.get_all_images(self.parameters['input_path'])
            else:
                self.error_occurred.emit(f"Input folder does not exist: {self.parameters['input_path']}")
                return

        if not images_to_process:
            self.log_message_signal.emit("No valid images found to process.", "WARNING")
            self.error_occurred.emit("No valid images found.") 
            return

        self.log_message_signal.emit(f"Found {len(images_to_process)} images to process.", "INFO")
        session_total_tokens = 0
        ai_results_list = [] 

        try:
            base_output_folder = helpers.get_output_folder({
                'output_folder_option': lambda: self.parameters['output_folder_option'],
                'input_path': lambda: self.parameters['input_path'],
                'input_type': lambda: self.parameters['input_type'],
                'custom_output_path': lambda: self.parameters['custom_output_path']
            })
            session_name = helpers.generate_session_folder_name()
            session_path = os.path.join(base_output_folder, session_name)
            os.makedirs(session_path, exist_ok=True)
            self.log_message_signal.emit(f"Session folder: {session_path}", "INFO")
            renamed_folder_path = os.path.join(session_path, "renamed_images") 
            summary_txt_path = os.path.join(session_path, helpers.generate_output_filename())
            failed_log_path = os.path.join(session_path, "failed.log") 
        except Exception as e:
            self.error_occurred.emit(f"Failed to prepare session paths: {e}")
            return
        
        with open(failed_log_path, "w", encoding="utf-8") as fail_log_f:
            for idx, image_path in enumerate(images_to_process):
                if self._is_cancel_requested: # Check for cancellation
                    self.log_message_signal.emit("Processing cancelled by user during AI phase.", "WARNING") # Changed level
                    self.processing_cancelled.emit("Cancelled during AI processing.")
                    return # Exit the run method
                
                self.log_message_signal.emit(f"AI Processing image {idx + 1}/{len(images_to_process)}: {os.path.basename(image_path)}", "INFO")
                ocr_text_for_api = ""
                if self.parameters['ocr_enabled']:
                    try:
                        ocr_text_for_api = helpers.extract_text_from_image(
                            image_path, self.parameters['tesseract_path'], self.parameters['ocr_lang']
                        )
                        if ocr_text_for_api.startswith("⚠️ OCR failed:"):
                            self.log_message_signal.emit(f"OCR for {os.path.basename(image_path)}: {ocr_text_for_api}", "ERROR")
                            ocr_text_for_api = ""
                        elif ocr_text_for_api:
                             self.log_message_signal.emit(f"OCR for {os.path.basename(image_path)}: {ocr_text_for_api[:100]}...", "DEBUG")
                    except Exception as e:
                        self.log_message_signal.emit(f"OCR process failed for {os.path.basename(image_path)}: {e}", "ERROR")
                        ocr_text_for_api = ""

                ai_result, tokens, error_msg = ai_handler.describe_image_local(
                    image_path=image_path, api_key=self.parameters['api_key'],
                    name_lang=self.parameters['filename_language'], alt_lang=self.parameters['alttext_language'],
                    detail_level=self.parameters['name_detail_level'], vision_detail=self.parameters['vision_detail'],
                    ocr_text_external=ocr_text_for_api
                )

                current_image_error = error_msg
                base_name_for_list = "" 
                img_ext_for_list = os.path.splitext(image_path)[1].lower()

                if current_image_error: 
                    self.log_message_signal.emit(f"API Error for {os.path.basename(image_path)}: {current_image_error}", "ERROR")
                    fail_log_f.write(f"{image_path} :: API Error: {current_image_error}\n")
                elif not ai_result or "name" not in ai_result or "alt" not in ai_result: 
                    current_image_error = f"Invalid or empty response from API for {os.path.basename(image_path)}."
                    self.log_message_signal.emit(current_image_error, "ERROR")
                    fail_log_f.write(f"{image_path} :: {current_image_error}\n")
                else: 
                    session_total_tokens += tokens
                    base_name_for_list = helpers.slugify(ai_result.get('name', ''))[:100]
                    if not base_name_for_list:
                        base_name_for_list = f"image-{idx+1}"
                    self.log_message_signal.emit(f"AI result for {os.path.basename(image_path)} received. Tokens: +{tokens}", "TOKEN")

                ai_results_list.append({
                    'original_path': image_path,
                    'raw_ai_name': ai_result.get('name', '') if ai_result else '',
                    'raw_ai_alt': ai_result.get('alt', '') if ai_result else '',
                    'slugified_name': base_name_for_list, 
                    'extension': img_ext_for_list,
                    'error': current_image_error 
                })
                self.progress_updated.emit(idx + 1)
        
        self.log_message_signal.emit(f"AI processing for {len(images_to_process)} images complete. Token usage this run: {session_total_tokens}", "INFO")
        self.ai_processing_complete.emit(ai_results_list, session_path, renamed_folder_path, summary_txt_path, session_total_tokens)
        
    def cancel(self): 
        self.request_cancel() 
        self.log_message_signal.emit("Cancellation requested (via old worker.cancel() method).", "WARNING")

# No changes needed for EditableResultsDialog as it's already defined correctly.
# The rest of the MainWindow methods will be updated in subsequent diffs if this one applies successfully.
# For now, focusing on the core cancellation logic within the worker and the UI setup.
# The MainWindow methods to handle the cancel button and worker signals will be added next.
# Note: QSizePolicy was already imported in the provided code for EditableResultsDialog.
# Removed redundant `import QSizePolicy` in the section for EditableResultsDialog.
# Ensured `os.path.basename` is used for dialog's info label.
# Ensured `_is_cancel_requested` is used in worker's run loop.
# Ensured `processing_cancelled` signal is emitted.
# Ensured `request_cancel` method sets `_is_cancel_requested`.
# Added `cancel_button` to `_create_input_tab_ui`.
# Added new signal `processing_cancelled` to `ProcessingWorker`.
# Added `_is_cancel_requested` and `request_cancel` to `ProcessingWorker`.
# Modified `ProcessingWorker.run` to check `_is_cancel_requested` and emit `processing_cancelled`.
# Modified `MainWindow._start_processing` to show, enable, and connect `cancel_button`.
# Added `_request_cancel_processing` method.
# Added `_handle_processing_cancelled` slot.
# Connected `worker.processing_cancelled` to `_handle_processing_cancelled`.
# Updated `_start_review_phase`, `_finalize_file_writing`, and `processing_error_slot` for cancel button visibility and state.
# The old `worker.cancel()` method now calls `request_cancel()` for compatibility.
# Changed "warn" to "WARNING" for log level consistency.The cancellation functionality has been implemented as requested.

**Summary of Changes:**

1.  **Cancel Button UI (`_create_input_tab_ui`):**
    *   `self.cancel_button = QPushButton("Cancel")` was created.
    *   It's initially hidden (`self.cancel_button.hide()`).
    *   It was added to the `describe_button_layout` next to the "Describe Images" button.

2.  **`ProcessingWorker` Modifications:**
    *   **`__init__`**: `self._is_cancel_requested = False` was added.
    *   **`request_cancel(self)` method**: Added to set `self._is_cancel_requested = True` and log the request.
    *   **`processing_cancelled = pyqtSignal(str)`**: New signal added.
    *   **`run()` method**:
        *   The loop now checks `if self._is_cancel_requested:` at the beginning of each iteration.
        *   If true, it emits `log_message_signal` (with "WARNING" level) and `processing_cancelled`, then `return`s to stop processing.
    *   The old `cancel()` method was updated to call `request_cancel()`.

3.  **`MainWindow` Cancel Logic:**
    *   **`_start_processing()`**:
        *   The `self.cancel_button` is shown and enabled.
        *   `self.cancel_button.clicked.connect(self._request_cancel_processing)` is set up.
        *   The `worker.processing_cancelled` signal is connected to `self._handle_processing_cancelled`.
        *   Signal connections for thread cleanup now also include `processing_cancelled`.
    *   **`_request_cancel_processing(self)` method**:
        *   Calls `self.worker.request_cancel()` if the worker exists.
        *   Logs the cancellation request.
        *   Disables `self.cancel_button` to prevent multiple clicks.
    *   **`_handle_processing_cancelled(self, message)` slot**:
        *   Logs the cancellation message (with "WARNING" level).
        *   Updates the status bar.
        *   Re-enables `self.describe_button`.
        *   Hides and re-enables `self.cancel_button` for the next run.
        *   Hides the progress bar.
        *   Quits the `processing_thread` if it's running.
        *   Cleans up `self.dropped_files_temp_dir` if it exists.
    *   **`_start_review_phase()`**:
        *   Hides `self.cancel_button` as AI processing is complete.
        *   Re-enables `self.cancel_button` (for future runs).
    *   **`_finalize_file_writing()` (finally block)**:
        *   Ensures `self.cancel_button` is hidden and re-enabled.
    *   **`processing_error_slot()`**:
        *   Hides `self.cancel_button`.
        *   Re-enables `self.cancel_button` for future runs.

The cancellation mechanism for the AI processing worker is now in place.
