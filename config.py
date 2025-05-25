"""
config.py

Handles saving and loading Altomatic's configuration:
- Stores user preferences (Tesseract path, encrypted OpenAI API key, etc.)
- Excludes temporary input paths
- Supports resetting to defaults
- Provides simple obfuscation for the API key
- Allows opening config folder
"""

import os
import json
import base64

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".altomatic_config.json")

# Basic prefix for naive obfuscation
SECRET_PREFIX = "ALTOMATIC:"

def obfuscate_api_key(plaintext: str) -> str:
    """
    Encodes SECRET_PREFIX + plaintext in base64 as a naive obfuscation.
    This is not real encryption, just simple hiding of the raw key.
    """
    raw = SECRET_PREFIX + plaintext
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")

def deobfuscate_api_key(ciphertext: str) -> str:
    """
    Decodes base64 and removes SECRET_PREFIX if present.
    Returns empty string if not valid or prefix not found.
    """
    try:
        data = base64.b64decode(ciphertext).decode("utf-8")
        if data.startswith(SECRET_PREFIX):
            return data[len(SECRET_PREFIX):]
        return ""
    except Exception:
        return ""

# Default configuration dictionary
DEFAULT_CONFIG = {
    'custom_output_path': "",
    'output_folder_option': "Same as input",
    'openai_api_key': "",  # will be obfuscated on disk
    'window_geometry': "900x600",
    'filename_language': "English",
    'alttext_language': "English",
    'name_detail_level': "Detailed",  # can be "Minimal" / "Normal" / "Detailed"
    'vision_detail': "auto",          # "low", "high", or "auto"
    'ocr_enabled': False,
    'ui_language': "English",
    'tesseract_path': "",
    'ocr_language': "eng",
    'ui_theme': "Light",
}

def load_config():
    """
    Loads the config from disk, or returns defaults if not found/broken.
    Deobfuscates the API key if present.
    """
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        # Deobfuscate the key
        if config['openai_api_key']:
            config['openai_api_key'] = deobfuscate_api_key(config['openai_api_key'])
        return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(settings_dict: dict, window_geometry_str: str):
    """
    Saves the relevant config keys to disk.
    Obfuscates the openai_api_key.
    'settings_dict' should contain all keys from DEFAULT_CONFIG except 'window_geometry'.
    'window_geometry_str' is a string like "900x600".
    """
    data_to_save = {}
    for key in DEFAULT_CONFIG:
        if key == 'window_geometry':
            data_to_save['window_geometry'] = window_geometry_str
        elif key == 'openai_api_key':
            # Ensure API key is present in settings_dict, even if empty
            plain_api_key = settings_dict.get('openai_api_key', '')
            data_to_save['openai_api_key'] = obfuscate_api_key(plain_api_key)
        elif key in settings_dict: # Check if key exists in provided dict
            data_to_save[key] = settings_dict[key]
        else:
            # If a key from DEFAULT_CONFIG is missing in settings_dict (should not happen if populated correctly)
            # save the default value for that key.
            data_to_save[key] = DEFAULT_CONFIG[key] 
            print(f"⚠️ Warning: Key '{key}' not found in settings_dict for saving. Using default.")


    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Could not save config: {e}")

def reset_config():
    """
    Deletes the config file entirely, forcing defaults on next run.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
        except Exception as e:
            print(f"⚠️ Could not delete config: {e}")

def open_config_folder():
    """
    Opens the folder containing the altomatic config file in the OS file explorer.
    """
    folder = os.path.dirname(CONFIG_FILE)
    if os.name == 'nt':
        os.startfile(folder)
    elif os.name == 'posix':
        import subprocess
        subprocess.call(["xdg-open", folder])
    else:
        print(f"Open config folder not implemented for OS: {os.name}")
