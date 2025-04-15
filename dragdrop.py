"""
dragdrop.py

Adds drag-and-drop support for input image/folder entry in Altomatic.
"""

import os
from tkinterdnd2 import DND_FILES
from helpers import get_image_count_in_folder
from ui_components import append_monitor_colored

def configure_drag_and_drop(root, state):
    """
    Registers drag-and-drop for the input entry widget,
    so the user can drop an image or a folder directly.
    """
    state['input_entry'].drop_target_register(DND_FILES)
    state['input_entry'].dnd_bind('<<Drop>>', lambda e: _handle_input_drop(e, state))

def _handle_input_drop(event, state):
    """
    Handles dropped file(s) or folder(s) onto the input entry.
    If a folder is dropped, we set input_type=Folder and path to that folder.
    If multiple files are dropped, we gather them into a 'Dropped Inputs' subfolder.
    """
    paths_list = event.widget.tk.splitlist(event.data)
    input_files = []

    for raw_path in paths_list:
        clean_path = raw_path.strip('{}')
        # If it's a folder, set it directly
        if os.path.isdir(clean_path):
            state['input_type'].set("Folder")
            state['input_path'].set(clean_path)
            count = get_image_count_in_folder(clean_path)
            state['image_count'].set(f"{count} image(s) found.")
            append_monitor_colored(state, f"[DRAGDROP] Folder dropped: {clean_path} ({count} images)", "info")
            return

        elif os.path.isfile(clean_path):
            input_files.append(clean_path)

    # If multiple files or a single file
    if input_files:
        if len(input_files) == 1:
            # Single file => set input_type=File
            state['input_type'].set("File")
            state['input_path'].set(input_files[0])
            state['image_count'].set("1 image selected.")
            append_monitor_colored(state, f"[DRAGDROP] Single file dropped: {input_files[0]}", "info")
        else:
            # Multiple files => create a 'Dropped Inputs' folder in same directory
            drop_folder = os.path.join(os.path.dirname(input_files[0]), "Dropped Inputs")
            os.makedirs(drop_folder, exist_ok=True)
            for img in input_files:
                basename = os.path.basename(img)
                target = os.path.join(drop_folder, basename)
                if not os.path.exists(target):
                    try:
                        os.link(img, target)
                    except Exception:
                        import shutil
                        shutil.copy(img, target)

            state['input_type'].set("Folder")
            state['input_path'].set(drop_folder)
            count = get_image_count_in_folder(drop_folder)
            state['image_count'].set(f"{count} image(s) dropped.")
            append_monitor_colored(state, f"[DRAGDROP] {len(input_files)} files => {drop_folder}", "info")
