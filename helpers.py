"""
helpers.py

Utility functions for Altomatic:
1. Converting an image file to a base64 data URL
2. Generating a short random ID (for folder or filename)
3. Creating session folder names with timestamp and random ID
4. Generating output filename with timestamp and random ID
5. Counting images in a folder
6. Resolving the user-chosen output folder
7. Slugify function for converting a text into a safe filename
8. Extracting text from an image with Tesseract OCR
"""

import os
import base64
from datetime import datetime
import random
import string

def generate_short_id(length=4):
    """
    Generates a short random ID consisting of uppercase letters and digits, e.g. 'A3F9'.
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def image_to_base64(path):
    """
    Converts the given image file to a base64-encoded data URL for sending to the OpenAI vision model.
    """
    ext = os.path.splitext(path)[1].lower().replace('.', '')
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{ext};base64,{encoded}"

def generate_session_folder_name():
    """
    Returns a folder name like: 'session-YYYY-MM-DD-HH-MM-[ID]'.
    Example: 'session-2025-04-15-19-37-A2B7'
    """
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    return f"session-{stamp}-{generate_short_id()}"

def generate_output_filename():
    """
    Returns a TXT filename like: 'altomatic-output-YYYY-MM-DD-HH-MM-[ID].txt'
    Example: 'altomatic-output-2025-04-15-19-37-A2B7.txt'
    """
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    return f"altomatic-output-{stamp}-{generate_short_id()}.txt"

def get_image_count_in_folder(folder):
    """
    Counts how many valid images (png, jpg, jpeg, webp) exist in a folder.
    """
    if not os.path.isdir(folder):
        return 0
    return len([
        f for f in os.listdir(folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ])

def get_all_images(folder):
    """
    Returns a list of valid images in the specified folder,
    ignoring non-image files and subfolders.
    """
    if not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ]

def get_output_folder(state):
    """
    Resolves which folder to use for output, based on user preferences.
    """
    preset = state['output_folder_option'].get()
    input_path = state['input_path'].get()
    input_type = state['input_type'].get()

    if preset == "Same as input":
        if input_type == "File":
            return os.path.dirname(input_path)
        return input_path
    elif preset == "Desktop":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif preset == "Pictures":
        return os.path.join(os.path.expanduser("~"), "Pictures")
    elif preset == "Custom":
        return state['custom_output_path'].get()
    # Default fallback
    return os.getcwd()

def slugify(text):
    """
    Converts a text to a safe lowercase string for filenames:
    1. Remove special characters
    2. Replace spaces with hyphens
    """
    import re
    text = text.strip().lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

def extract_text_from_image(image_path, tesseract_path="", lang="eng"):
    """
    Uses Tesseract OCR to extract text from an image.
    If tesseract_path is provided, sets it as the pytesseract command path.
    The 'lang' parameter is the Tesseract language code, e.g. 'eng', 'fas', etc.
    Returns the extracted text, or an error message starting with '⚠️ OCR failed:'.
    """
    try:
        from PIL import Image
        import pytesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception as e:
        return f"⚠️ OCR failed: {e}"
