"""
logic.py

Coordinates the main loop of image processing in Altomatic:
- Iterates over the images specified by the user
- Calls describe_image() from ai_handler
- Saves results in a new session folder
- Tracks total token usage
- Optionally keeps a global image count
"""

import os
import shutil
from tkinter import messagebox
from ai_handler import describe_image
from helpers import (
    get_all_images,
    get_output_folder,
    generate_session_folder_name,
    generate_output_filename,
    slugify
)
from ui_components import append_monitor_colored

def process_images(state):
    """
    Processes the images indicated by state['input_path'] and state['input_type'].
    1) Resolves the images to be processed (single file or entire folder).
    2) Creates a session folder, including a 'renamed_images' subfolder.
    3) For each image, calls describe_image(), saves the renamed copy, logs usage.
    4) Summarizes results in a text file, and logs them to the monitor and a messagebox.
    5) If 'global_images_count' is present, increments it by the number of processed images.
    """

    # Check for API Key
    api_key = state['openai_api_key'].get().strip()
    if not api_key:
        append_monitor_colored(state, "[ERROR] Missing API Key.", "error")
        messagebox.showerror("Missing API Key", "Please enter your OpenAI API key in the Settings tab.")
        return

    # Validate input path
    in_path = state['input_path'].get()
    if not os.path.exists(in_path):
        append_monitor_colored(state, "[ERROR] Input path does not exist.", "error")
        messagebox.showerror("Invalid Input", "Input path does not exist.")
        return

    # Gather images (single or multiple)
    if state['input_type'].get() == "File":
        images = [in_path]
    else:
        images = get_all_images(in_path)
    if not images:
        append_monitor_colored(state, "[WARN] No valid images found.", "warn")
        messagebox.showwarning("No Images", "No valid image files found.")
        return

    append_monitor_colored(state, f"[INFO] Found {len(images)} images to process.", "info")

    # Reset total tokens for this run
    state['total_tokens'].set(0)

    # Create session folder
    base_output_folder = get_output_folder(state)
    session_name = generate_session_folder_name()
    session_path = os.path.join(base_output_folder, session_name)
    os.makedirs(session_path, exist_ok=True)
    append_monitor_colored(state, f"[INFO] Session folder: {session_path}", "info")

    renamed_folder = os.path.join(session_path, "renamed_images")
    os.makedirs(renamed_folder, exist_ok=True)

    txt_file_path = os.path.join(session_path, generate_output_filename())
    log_file_path = os.path.join(session_path, "failed.log")

    # Setup progress bar
    state['progress_bar']['maximum'] = len(images)
    state['progress_bar']['value'] = 0

    # Possibly track global images
    if 'global_images_count' not in state:
        from tkinter import IntVar
        state['global_images_count'] = IntVar(value=0)

    with open(txt_file_path, "w", encoding="utf-8") as txt_f, open(log_file_path, "w", encoding="utf-8") as log_f:
        for idx, img_path in enumerate(images):
            try:
                append_monitor_colored(state, f"[PROCESS] Analyzing {img_path}", "info")
                result = describe_image(state, img_path)

                # Validate model response
                if not result or "name" not in result or "alt" not in result:
                    raise ValueError("Invalid or empty response from the model.")

                # Construct new filename from 'name'
                base_name = slugify(result['name'])[:100]
                if not base_name:
                    base_name = f"image-{idx+1}"

                ext = os.path.splitext(img_path)[1].lower()
                new_name = f"{base_name}{ext}"
                new_path = os.path.join(renamed_folder, new_name)

                # Copy (or rename) the file
                shutil.copy(img_path, new_path)

                # Write to the summary text file
                txt_f.write(f"[Original: {os.path.basename(img_path)}]\n")
                txt_f.write(f"Name: {base_name}\n")
                txt_f.write(f"Alt: {result['alt']}\n\n")

                append_monitor_colored(state, f"[SUCCESS] -> {new_name}", "success")

            except Exception as e:
                log_f.write(f"{img_path} :: {e}\n")
                append_monitor_colored(state, f"[FAIL] {img_path} :: {e}", "error")
                print(f"⚠️ Failed to process {img_path}: {e}")

            # Update progress
            state['progress_bar']['value'] = idx + 1
            state['progress_bar'].update_idletasks()

    # Update global count
    old_count = state['global_images_count'].get()
    new_count = old_count + len(images)
    state['global_images_count'].set(new_count)

    total_tokens = state['total_tokens'].get()
    msg = (
        f"✅ Processed {len(images)} image(s).\n"
        f"Session folder: {session_path}\n"
        f"Output file: {os.path.basename(txt_file_path)}\n\n"
        f"Token usage this run: {total_tokens}\n"
        f"Total images analyzed overall: {new_count}"
    )
    append_monitor_colored(state, "[PROCESS END] " + msg.replace("\n"," | "), "info")
    messagebox.showinfo("Done", msg)
