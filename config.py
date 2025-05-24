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
    'total_accumulated_tokens': 0, # New key for tracking all-time token usage
    'ai_model': 'gpt-4.1-nano', # New key for AI model selection
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

def save_config(config_data, window_geometry_str=None):
    """
    Saves the current settings from the 'config_data' dictionary to CONFIG_FILE.
    API key is obfuscated.
    'config_data' should be a dictionary with direct values.
    'window_geometry_str' is an optional string like "800x600".
    """
    data_to_save = {}
    # Iterate over keys in config_data plus keys in DEFAULT_CONFIG to ensure all are covered
    all_keys = set(config_data.keys()) | set(DEFAULT_CONFIG.keys())

    for key in all_keys:
        if key == 'window_geometry': # Skip, handled by window_geometry_str later
            continue
        
        value = config_data.get(key)

        if key == 'openai_api_key':
            # Expects plain API key, will be encoded.
            # If value is None (key not in config_data), encode as empty string from DEFAULT_CONFIG.
            plain_api_key = value if value is not None else DEFAULT_CONFIG.get(key, "")
            data_to_save[key] = obfuscate_api_key(plain_api_key) if plain_api_key else ""
        elif value is not None: # For other keys, save if value is provided in config_data
            data_to_save[key] = value
        elif key in DEFAULT_CONFIG: # If key from DEFAULT_CONFIG is missing in config_data, save the default.
            data_to_save[key] = DEFAULT_CONFIG[key]
        # If a key is in config_data but not in DEFAULT_CONFIG and not None, it's saved.
        # If a key is not in config_data and not in DEFAULT_CONFIG, it's ignored.

    # Handle window_geometry separately
    if window_geometry_str:
        data_to_save['window_geometry'] = window_geometry_str
    elif 'window_geometry' in config_data and config_data['window_geometry'] is not None: 
        data_to_save['window_geometry'] = config_data['window_geometry']
    elif 'window_geometry' in DEFAULT_CONFIG: # Ensure it's always set if not provided
        data_to_save['window_geometry'] = DEFAULT_CONFIG['window_geometry']
    else: # Fallback if not in DEFAULT_CONFIG for some reason
        data_to_save['window_geometry'] = "900x600"


    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
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
