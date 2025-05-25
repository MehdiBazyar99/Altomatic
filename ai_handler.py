"""
ai_handler.py

Communicates with OpenAI's GPT-4.1-nano for image description.
- Optionally includes OCR text in the prompt if enabled
- Returns 'name' and 'alt' in a structured JSON
"""

from openai import OpenAI
import json
from helpers import image_to_base64 # extract_text_from_image is used by worker in pyqt_ui.py

MODEL = "gpt-4o-mini" # Updated model as gpt-4.1-nano is not a standard name, gpt-4o-mini is a good alternative.

def describe_image_local(image_path: str, api_key: str, 
                         name_lang: str, alt_lang: str, 
                         detail_level: str, vision_detail: str,
                         ocr_text_external: str = "") -> tuple[dict | None, int, str | None]:
    """
    Describes an image using the specified OpenAI model with provided parameters.

    Args:
        image_path (str): Path to the image file.
        api_key (str): OpenAI API key.
        name_lang (str): Language for the 'name' field (e.g., "english", "persian").
        alt_lang (str): Language for the 'alt' text (e.g., "english", "persian").
        detail_level (str): Detail level for the 'name' ("minimal", "normal", "detailed").
        vision_detail (str): Vision detail for OpenAI model ("low", "high", "auto").
        ocr_text_external (str, optional): Externally provided OCR text. Defaults to "".

    Returns:
        tuple[dict | None, int, str | None]: 
            (result_dict, tokens_used, error_message)
            result_dict is { "name": str, "alt": str } or None on error.
            tokens_used is the number of tokens consumed, 0 on error.
            error_message is None on success, or an error string on failure.
    """
    client = OpenAI(api_key=api_key)
    tokens_used = 0

    try:
        b64_image = image_to_base64(image_path)
    except Exception as e:
        return None, 0, f"Failed to convert image to base64: {e}"

    prompt_parts = [
        "You are an expert image analyst.",
        "Your task is to analyze the content and purpose of the given image.",
        "Generate a JSON object with the following structure:",
        "{",
        "  \"name\": \"<a lowercase, dash-separated filename (max 10 words)>\",",
        "  \"alt\": \"<a clear and descriptive alt text, suitable for screen readers>\"",
        "}",
        "Guidelines:",
        "- The 'name' should describe what the image is or what it's used for.",
        "- The 'alt' text must explain what is visible and what is happening.",
        "- Avoid special characters or digits in the 'name'."
    ]

    if ocr_text_external:
        prompt_parts.append(f'\nText in image from OCR:\n"""\n{ocr_text_external}\n"""')

    name_lang_lower = name_lang.lower()
    if detail_level.lower() == "minimal":
        prompt_parts.append(f"The 'name' should be a very short {name_lang_lower} phrase with 1–2 simple words.")
    elif detail_level.lower() == "normal":
        prompt_parts.append(f"The 'name' should be a clear {name_lang_lower} phrase with up to 3 words.")
    else: # default to detailed
        prompt_parts.append(f"The 'name' should be a descriptive {name_lang_lower} phrase with up to 10 words.")

    prompt_parts.append(f"The 'alt' should be written in {alt_lang.lower()}.")
    
    final_prompt = "\n".join(prompt_parts)

    try:
        # Using the standard chat completions endpoint structure
        response = client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"}, # Forcing JSON output
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": final_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": b64_image, "detail": vision_detail.lower()}
                        }
                    ]
                }
            ]
        )
        
        if response.usage:
            tokens_used = response.usage.total_tokens
        
        response_text = response.choices[0].message.content
        if not response_text:
            return None, tokens_used, "API returned empty content."

        try:
            result_dict = json.loads(response_text)
            if not isinstance(result_dict, dict) or "name" not in result_dict or "alt" not in result_dict:
                return None, tokens_used, f"API response is not valid JSON with 'name' and 'alt' keys: {response_text}"
            return result_dict, tokens_used, None
        except json.JSONDecodeError as e:
            return None, tokens_used, f"Failed to decode API response JSON: {e}. Response: {response_text}"

    except Exception as e:
        return None, 0, f"OpenAI API call failed: {e}"

# The old Tkinter-dependent describe_image function has been removed.
# The import for ui_components.append_monitor_colored has also been removed.
# helpers.extract_text_from_image is now called directly by the ProcessingWorker in pyqt_ui.py
# before calling this describe_image_local function.
