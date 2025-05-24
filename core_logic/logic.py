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
from .ai_handler import describe_image
from .helpers import (
    get_all_images,
    get_output_folder,
    generate_session_folder_name,
    generate_output_filename,
    slugify
)

def process_images(logger, state):
    """
    Processes the images indicated by state['input_path'] and state['input_type'].
    1) Resolves the images to be processed (single file or entire folder).
    2) Creates a session folder, including a 'renamed_images' subfolder.
    3) For each image, calls describe_image(), saves the renamed copy, logs usage.
    4) Summarizes results in a text file and returns a summary dictionary.
    5) If 'global_images_count' is present, increments it by the number of processed images.
    """
    processed_count = 0
    errors_encountered = 0
    session_path = None # Initialize session_path

    # Check for API Key
    api_key = state['openai_api_key'].get().strip()
    if not api_key:
        logger.error("[ERROR] Missing API Key. Please enter your OpenAI API key in the Settings tab.")
        return {
            "processed_count": 0,
            "total_images": 0,
            "session_folder_path": None,
            "total_tokens_session": state['total_tokens'].get() if 'total_tokens' in state else 0,
            "errors_encountered": 1, # Generic error for missing API key
            "summary_message": "Error: Missing API Key."
        }

    # Validate input path
    in_path = state['input_path'].get()
    if not os.path.exists(in_path):
        logger.error("[ERROR] Input path does not exist.")
        return {
            "processed_count": 0,
            "total_images": 0,
            "session_folder_path": None,
            "total_tokens_session": state['total_tokens'].get() if 'total_tokens' in state else 0,
            "errors_encountered": 1, # Generic error for invalid path
            "summary_message": "Error: Input path does not exist."
        }

    # Gather images (single or multiple)
    if state['input_type'].get() == "File":
        images = [in_path]
    else:
        images = get_all_images(in_path)

    total_images = len(images)

    if not images:
        logger.warn("[WARN] No valid images found.")
        return {
            "processed_count": 0,
            "total_images": 0,
            "session_folder_path": None,
            "total_tokens_session": state['total_tokens'].get() if 'total_tokens' in state else 0,
            "errors_encountered": 0, # No errors, just no images
            "summary_message": "Warning: No valid images found."
        }

    logger.info(f"[INFO] Found {total_images} images to process.")

    # Reset total tokens for this run if the variable exists in state
    if 'total_tokens' in state:
        state['total_tokens'].set(0)

    # Create session folder
    base_output_folder = get_output_folder(state)
    session_name = generate_session_folder_name()
    session_path = os.path.join(base_output_folder, session_name)
    os.makedirs(session_path, exist_ok=True)
    logger.info(f"[INFO] Session folder: {session_path}")

    renamed_folder = os.path.join(session_path, "renamed_images")
    os.makedirs(renamed_folder, exist_ok=True)

    txt_file_path = os.path.join(session_path, generate_output_filename())
    log_file_path = os.path.join(session_path, "failed.log")

    # Possibly track global images - this part might need reconsideration
    # as Tkinter specific IntVar is used. For now, we assume it's handled if present.
    # If 'global_images_count' is critical, its handling should be abstracted from Tkinter.
    # For this refactor, we'll keep the logic if state['global_images_count'] exists.
    global_images_count_exists = 'global_images_count' in state

    with open(txt_file_path, "w", encoding="utf-8") as txt_f, open(log_file_path, "w", encoding="utf-8") as log_f:
        for idx, img_path in enumerate(images):
            try:
                logger.info(f"[PROCESS] Analyzing {img_path}")
                # Pass logger to describe_image
                result = describe_image(logger, state, img_path)

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

                shutil.copy(img_path, new_path)

                txt_f.write(f"[Original: {os.path.basename(img_path)}]\n")
                txt_f.write(f"Name: {base_name}\n")
                txt_f.write(f"Alt: {result['alt']}\n\n")

                logger.info(f"[SUCCESS] -> {new_name}") # Changed from "success" to "info" for logger
                processed_count += 1

            except Exception as e:
                log_f.write(f"{img_path} :: {e}\n")
                logger.error(f"[FAIL] {img_path} :: {e}")
                # print(f"⚠️ Failed to process {img_path}: {e}") # Replaced by logger
                errors_encountered +=1

            # Progress bar updates removed

    # Update global count if applicable
    new_total_global_images = None
    if global_images_count_exists:
        old_count = state['global_images_count'].get()
        new_total_global_images = old_count + processed_count # Only count successfully processed
        state['global_images_count'].set(new_total_global_images)

    total_tokens_session = state['total_tokens'].get() if 'total_tokens' in state else 0
    
    summary_message = (
        f"✅ Processed {processed_count}/{total_images} image(s).\n"
        f"Session folder: {session_path}\n"
        f"Output file: {os.path.basename(txt_file_path)}\n"
        f"Errors encountered: {errors_encountered}\n\n"
        f"Token usage this run: {total_tokens_session}\n"
    )
    if new_total_global_images is not None:
        summary_message += f"Total images analyzed overall: {new_total_global_images}"

    logger.info("[PROCESS END] " + summary_message.replace("\n"," | "))
    
    # Prepare the detailed summary dictionary for return
    summary_data = {
        "message": summary_message.strip(),
        "images_processed_this_run": processed_count, # Number of successfully processed images
        "total_images_in_batch": total_images, # Total images attempted
        "tokens_used_this_run": total_tokens_session, # Tokens used in this specific run
        "updated_global_images_count": state.get('global_images_count', 0), # Current global count from state
        "session_folder_path": session_path,
        "output_file_path": txt_file_path, # Path to the summary text file
        "errors_encountered": errors_encountered
    }
    return summary_data
