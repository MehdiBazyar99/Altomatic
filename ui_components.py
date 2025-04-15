"""
ui_components.py

Builds the main UI for Altomatic, with:
- Tabs (Input, Output, Settings)
- A separate floating Monitor window for logs
- Additional UI controls for:
  - Clearing / copying logs
  - Resetting token usage, resetting global stats
  - Opening config folder
  - Selecting UI theme
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyperclip

from config import save_config, open_config_folder
from helpers import get_image_count_in_folder

################################################################################
# MAIN BUILD_UI
################################################################################

def build_ui(root, user_config):
    """
    Builds the main UI structure (tabs: Input, Output, Settings).
    Returns a 'state' dictionary containing references to variables and widgets.
    """
    root.geometry("420x670")
    main_frame = ttk.Frame(root, padding=10)
    main_frame.grid(row=0, column=0, sticky='nsew')
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(1, weight=1)

    # Menubar
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # Notebook for tabs
    notebook = ttk.Notebook(main_frame)
    notebook.grid(row=0, column=0, sticky='nsew')
    main_frame.rowconfigure(0, weight=1)

    # The dictionary holding references to UI variables and states
    state = {
        # Input
        'input_type':        tk.StringVar(value="Folder"),
        'input_path':        tk.StringVar(value=""),
        'image_count':       tk.StringVar(value=''),

        # Output
        'custom_output_path': tk.StringVar(value=user_config.get('custom_output_path', "")),
        'output_folder_option': tk.StringVar(value=user_config.get('output_folder_option', "Same as input")),

        # Settings
        'openai_api_key':    tk.StringVar(value=user_config.get('openai_api_key', "")),
        'filename_language': tk.StringVar(value=user_config.get('filename_language', "English")),
        'alttext_language':  tk.StringVar(value=user_config.get('alttext_language', "English")),
        'name_detail_level': tk.StringVar(value=user_config.get('name_detail_level', "Detailed")),
        'vision_detail':     tk.StringVar(value=user_config.get('vision_detail', "auto")),
        'ocr_enabled':       tk.BooleanVar(value=user_config.get('ocr_enabled', False)),
        'ui_language':       tk.StringVar(value=user_config.get('ui_language', "English")),
        'tesseract_path':    tk.StringVar(value=user_config.get('tesseract_path', "")),
        'ocr_language':      tk.StringVar(value=user_config.get('ocr_language', "eng")),
        'ui_theme':          tk.StringVar(value=user_config.get('ui_theme', "Light")),

        # Logs and monitor
        'logs': [],
        'monitor_window': None,
        'monitor_text': None,

        # Token usage
        'total_tokens': tk.IntVar(value=0),

        # menubar
        'menubar': menubar
    }

    # Create tabs: Input, Output, Settings
    tab_input = ttk.Frame(notebook, padding=10)
    tab_output = ttk.Frame(notebook, padding=10)
    tab_settings = ttk.Frame(notebook, padding=10)

    notebook.add(tab_input, text="Input")
    notebook.add(tab_output, text="Output")
    notebook.add(tab_settings, text="Settings")

    # Fill each tab
    _build_tab_input(tab_input, state)
    _build_tab_output(tab_output, state)
    _build_tab_settings(tab_settings, state)

    # In the Output tab, let's place a label to show token usage
    state['lbl_token_usage'] = ttk.Label(tab_output, text="Tokens used: 0")
    state['lbl_token_usage'].grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=10)

    # Status bar (bottom)
    status_frame = ttk.Frame(main_frame)
    status_frame.grid(row=1, column=0, sticky='ew', pady=(5,0))
    status_frame.columnconfigure(1, weight=1)

    lbl_count = ttk.Label(status_frame, textvariable=state['image_count'], foreground="blue")
    lbl_count.grid(row=0, column=0, padx=(5,5))
    state['progress_bar'] = ttk.Progressbar(status_frame, mode='determinate')
    state['progress_bar'].grid(row=0, column=1, sticky='ew', padx=5, pady=2)

    # Build menubar
    _build_menus(menubar, root, state)

    return state

################################################################################
# MENUS
################################################################################

def _build_menus(menubar, root, state):
    """
    Adds 'File' and 'Monitor' and 'Help' menus to the menubar.
    """
    filemenu = tk.Menu(menubar, tearoff=False)
    filemenu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=filemenu)

    # Add a Monitor menu item
    monitor_menu = tk.Menu(menubar, tearoff=False)
    monitor_menu.add_command(label="Open Monitor", command=lambda: show_monitor_window(state))
    menubar.add_cascade(label="Monitor", menu=monitor_menu)

    # Help menu
    helpmenu = tk.Menu(menubar, tearoff=False)
    helpmenu.add_command(label="About", command=lambda: _show_about(root))
    menubar.add_cascade(label="Help", menu=helpmenu)

################################################################################
# TABS: INPUT
################################################################################

def _build_tab_input(frame, state):
    frame.columnconfigure(1, weight=1)
    row = 0

    ttk.Label(frame, text="Input Type:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
    om_input_type = ttk.OptionMenu(frame, state['input_type'], state['input_type'].get(), "Folder", "File")
    om_input_type.grid(row=row, column=1, sticky='w', padx=5, pady=2)

    row += 1
    ttk.Label(frame, text="Input Path:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
    input_entry = ttk.Entry(frame, textvariable=state['input_path'], width=50)
    input_entry.grid(row=row, column=1, sticky='ew', padx=5, pady=2)
    state['input_entry'] = input_entry  # for drag&drop
    ttk.Button(frame, text="Browse", command=lambda: _select_input(state)).grid(row=row, column=2, padx=5, pady=2)

    row += 1
    process_btn = ttk.Button(frame, text="Describe Images")
    process_btn.grid(row=row, column=1, pady=10)
    state['process_button'] = process_btn

################################################################################
# TABS: OUTPUT
################################################################################

def _build_tab_output(frame, state):
    frame.columnconfigure(1, weight=1)
    row = 0

    ttk.Label(frame, text="Save to:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
    om_output_folder = ttk.OptionMenu(
        frame,
        state['output_folder_option'],
        state['output_folder_option'].get(),
        "Same as input",
        "Pictures",
        "Desktop",
        "Custom"
    )
    om_output_folder.grid(row=row, column=1, sticky='w', padx=5, pady=2)

    row += 1
    ttk.Label(frame, text="Custom Folder:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
    custom_out_entry = ttk.Entry(frame, textvariable=state['custom_output_path'], width=50)
    custom_out_entry.grid(row=row, column=1, sticky='ew', padx=5, pady=2)
    ttk.Button(frame, text="Browse", command=lambda: _select_output_folder(state)).grid(row=row, column=2, padx=5, pady=2)

    # A label for token usage is placed in build_ui at the end

################################################################################
# TABS: SETTINGS
################################################################################

def _build_tab_settings(frame, state):
    frame.columnconfigure(1, weight=1)
    row = 0

    # 1) API Key
    ttk.Label(frame, text="OpenAI API Key:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    ttk.Entry(frame, textvariable=state['openai_api_key'], show='*', width=50).grid(row=row, column=1, padx=5, pady=5)

    row += 1
    # Save settings
    ttk.Button(frame, text="Save Settings", command=lambda: _save_settings(state)).grid(row=row, column=1, sticky='e', padx=5, pady=(10,5))

    row += 1
    # Reset defaults
    ttk.Button(frame, text="Reset Defaults", command=lambda: state['reset_config_callback']()).grid(row=row, column=1, sticky='e', padx=5, pady=(5,10))

    row += 1
    # Open config folder
    ttk.Button(frame, text="Open Config Folder", command=lambda: open_config_folder()).grid(row=row, column=1, sticky='e', padx=5, pady=5)

    # 2) UI Theme
    row += 1
    ttk.Label(frame, text="UI Theme:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    ttk.OptionMenu(
        frame,
        state['ui_theme'],
        state['ui_theme'].get(),
        "Light", "Dark", "BlueGray", "Solarized", "Pinky"
    ).grid(row=row, column=1, sticky='w')

    # 3) Filename Language
    row += 1
    ttk.Label(frame, text="Filename Language:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    ttk.OptionMenu(
        frame,
        state['filename_language'],
        state['filename_language'].get(),
        "English", "Persian"
    ).grid(row=row, column=1, sticky='w')

    # 4) Alt Text Language
    row += 1
    ttk.Label(frame, text="Alt Text Language:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    ttk.OptionMenu(
        frame,
        state['alttext_language'],
        state['alttext_language'].get(),
        "English", "Persian"
    ).grid(row=row, column=1, sticky='w')

    # 5) Name Detail Level
    row += 1
    ttk.Label(frame, text="Name Detail Level:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    ttk.OptionMenu(
        frame,
        state['name_detail_level'],
        state['name_detail_level'].get(),
        "Minimal", "Normal", "Detailed"
    ).grid(row=row, column=1, sticky='w')

    # 6) Vision detail
    row += 1
    ttk.Label(frame, text="Image Vision Detail:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    ttk.OptionMenu(
        frame,
        state['vision_detail'],
        state['vision_detail'].get(),
        "low", "high", "auto"
    ).grid(row=row, column=1, sticky='w')

    # 7) OCR
    row += 1
    ocr_checkbox = ttk.Checkbutton(
        frame,
        text="Enable OCR",
        variable=state['ocr_enabled']
    )
    ocr_checkbox.grid(row=row, column=1, sticky='w', padx=5, pady=5)

    row += 1
    ttk.Label(frame, text="Tesseract Path:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    tess_entry = ttk.Entry(frame, textvariable=state['tesseract_path'], width=40)
    tess_entry.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
    ttk.Button(frame, text="Browse", command=lambda: _browse_tesseract(state)).grid(row=row, column=2, padx=5, pady=5)

    row += 1
    ttk.Label(frame, text="OCR Language:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
    ttk.Entry(frame, textvariable=state['ocr_language'], width=10).grid(row=row, column=1, sticky='w', padx=5, pady=5)

    # 8) Reset token usage & stats
    row += 1
    ttk.Button(frame, text="Reset Token Usage", command=lambda: _reset_token_usage(state)).grid(row=row, column=1, sticky='e', padx=5, pady=5)
    row += 1
    ttk.Button(frame, text="Reset Analyzed Stats", command=lambda: _reset_global_stats(state)).grid(row=row, column=1, sticky='e', padx=5, pady=5)

################################################################################
# HELPER FUNCTIONS FOR TABS
################################################################################

def _select_input(state):
    """
    Lets the user pick either a folder or a single file, based on input_type.
    """
    if state['input_type'].get() == "Folder":
        path = filedialog.askdirectory()
    else:
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")])
    if path:
        state['input_path'].set(path)
        if state['input_type'].get() == "Folder":
            count = get_image_count_in_folder(path)
        else:
            count = 1
        state['image_count'].set(f"{count} image(s) selected.")

def _select_output_folder(state):
    path = filedialog.askdirectory()
    if path:
        state['custom_output_path'].set(path)

def _browse_tesseract(state):
    """
    Let the user pick the Tesseract executable file.
    """
    path = filedialog.askopenfilename(filetypes=[("Tesseract Executable", "tesseract.exe")])
    if path:
        state['tesseract_path'].set(path)

def _save_settings(state):
    """
    Saves config, re-applies theme if changed.
    """
    geometry = state['root'].winfo_geometry()
    from config import save_config
    save_config(state, geometry)

    # Re-apply theme
    new_theme = state['ui_theme'].get()
    from main import apply_theme
    apply_theme(state['root'], new_theme)

    messagebox.showinfo("Saved", "✅ Settings saved successfully.")

def _reset_token_usage(state):
    """
    Reset the total token usage to 0.
    """
    state['total_tokens'].set(0)
    if 'lbl_token_usage' in state:
        state['lbl_token_usage'].config(text="Tokens used: 0")
    append_monitor_colored(state, "Token usage reset to 0", "warn")

def _reset_global_stats(state):
    """
    If there's a global_images_count or other stats, reset them to zero.
    """
    if 'global_images_count' in state:
        state['global_images_count'].set(0)
        append_monitor_colored(state, "Global images analyzed count reset to 0", "warn")
    else:
        append_monitor_colored(state, "No global_images_count found to reset", "warn")

################################################################################
# MONITOR WINDOW
################################################################################

def show_monitor_window(state):
    """
    Opens a separate floating window with a text widget to display logs in color.
    """
    if state['monitor_window'] and tk.Toplevel.winfo_exists(state['monitor_window']):
        # If already open, bring it to front
        state['monitor_window'].lift()
        return

    win = tk.Toplevel()
    win.title("Monitor")
    win.geometry("950x500")
    win.resizable(True, True)

    text_area = tk.Text(win, wrap='word')
    text_area.pack(side='left', fill='both', expand=True)
    scrollbar = ttk.Scrollbar(win, command=text_area.yview)
    scrollbar.pack(side='right', fill='y')
    text_area['yscrollcommand'] = scrollbar.set

    # Tag configurations for color-coded logging
    text_area.tag_config("info", foreground="blue")
    text_area.tag_config("warn", foreground="orange")
    text_area.tag_config("error", foreground="red")
    text_area.tag_config("success", foreground="green")
    text_area.tag_config("debug", foreground="purple")
    text_area.tag_config("token", foreground="#009688")

    # Buttons for clearing and copying logs
    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill='x')
    clear_btn = ttk.Button(btn_frame, text="Clear", command=lambda: _clear_monitor(state))
    clear_btn.pack(side='left', padx=5, pady=2)
    copy_btn = ttk.Button(btn_frame, text="Copy", command=lambda: _copy_monitor(state))
    copy_btn.pack(side='left', padx=5, pady=2)

    state['monitor_window'] = win
    state['monitor_text'] = text_area

    # Show existing logs
    for msg in state['logs']:
        _write_monitor_line_colored(state, msg)

def _clear_monitor(state):
    """
    Clears both the in-memory logs and the text widget content.
    """
    state['logs'].clear()
    if state['monitor_text']:
        state['monitor_text'].delete('1.0', 'end')

def _copy_monitor(state):
    """
    Copies the entire monitor text to the clipboard.
    """
    text = ""
    if state['monitor_text']:
        text = state['monitor_text'].get('1.0', 'end')
    pyperclip.copy(text)
    messagebox.showinfo("Copied", "Log text copied to clipboard.")

def append_monitor_colored(state, message: str, level: str = "info"):
    """
    Appends a message to logs and writes it in the text widget with a color tag.
    level can be: 'info', 'warn', 'error', 'success', 'debug', 'token'
    """
    formatted = f"[{level.upper()}] {message}"
    state['logs'].append((formatted, level))
    _write_monitor_line_colored(state, (formatted, level))

def _write_monitor_line_colored(state, log_item):
    """
    Writes a single line to the monitor text widget with color coding.
    """
    if not state['monitor_text']:
        return
    text_widget = state['monitor_text']
    text, level = log_item
    text_widget.config(state='normal')
    text_widget.insert('end', text + '\n', level)
    text_widget.see('end')
    text_widget.config(state='disabled')

################################################################################
# ABOUT DIALOG
################################################################################

def _show_about(root):
    """
    Displays a simple 'About' dialog with a link to GitHub.
    """
    import webbrowser
    top = tk.Toplevel(root)
    top.title("About Altomatic")
    top.geometry("420x220")
    top.resizable(False, False)

    ttk.Label(top, text="Altomatic", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
    ttk.Label(
        top,
        text="Created by Mehdi\n\nAn image captioning tool powered by GPT-4.1-nano.\n"
             "Name and describe your images with AI.\n\n"
    ).pack()

    def open_github():
        webbrowser.open_new("https://github.com/MehdiDevX")

    link = ttk.Label(top, text="Visit GitHub Repository", foreground="blue", cursor="hand2")
    link.pack()
    link.bind("<Button-1>", lambda e: open_github())

    ttk.Button(top, text="Close", command=top.destroy).pack(pady=10)
