"""
ai_handler.py

Communicates with OpenAI's GPT-4.1-nano for image description.
- Optionally includes OCR text in the prompt if enabled
- Returns 'name' and 'alt' in a structured JSON
- Logs usage tokens (if available) and accumulates them in state['total_tokens']
"""

from openai import OpenAI
import json
from helpers import image_to_base64, extract_text_from_image
from ui_components import append_monitor_colored

MODEL = "gpt-4.1-nano"

def describe_image(state, image_path: str) -> dict | None:
    """
    Describes the image using GPT-4.1-nano, reading user settings from 'state'.
    
    - If OCR is enabled, extracts text with Tesseract and appends that text to the prompt.
    - Builds a JSON structure prompt asking for {"name": ..., "alt": ...}.
    - If response.usage is available, logs the token usage and adds to state['total_tokens'].
    
    Returns:
        A dict { "name": str, "alt": str }
        or None if there's an error or invalid response.
    """
    # Gather relevant config from state
    api_key = state['openai_api_key'].get()
    name_lang = state['filename_language'].get().lower()   # e.g. "english", "persian"
    alt_lang = state['alttext_language'].get().lower()     # e.g. "english", "persian"
    detail_level = state['name_detail_level'].get().lower()# "minimal"/"normal"/"detailed"
    vision_detail = state['vision_detail'].get().lower()   # "low"/"high"/"auto"
    ocr_enabled = state['ocr_enabled'].get()
    tesseract_path = state['tesseract_path'].get()
    ocr_lang = state['ocr_language'].get()

    client = OpenAI(api_key=api_key)

    # If OCR is enabled, attempt to extract text
    if ocr_enabled:
        ocr_result = extract_text_from_image(image_path, tesseract_path, ocr_lang)
        if ocr_result.startswith("⚠️ OCR failed:"):
            # Log error but continue with empty OCR text
            append_monitor_colored(state, ocr_result, "error")
            ocr_text = ""
        else:
            append_monitor_colored(state, f"[OCR RESULT] {ocr_result}", "warn")
            ocr_text = ocr_result
    else:
        ocr_text = ""

    # Convert image to base64
    b64_image = image_to_base64(image_path)

    # Build the prompt
    prompt = (
        "You are an expert image analyst.\n"
        "Your task is to analyze the content and purpose of the given image.\n\n"
        "Generate a JSON object with the following structure:\n"
        "{\n"
        "  \"name\": \"<a lowercase, dash-separated filename (max 10 words)>\",\n"
        "  \"alt\": \"<a clear and descriptive alt text, suitable for screen readers>\"\n"
        "}\n\n"
        "Guidelines:\n"
        "- The 'name' should describe what the image is or what it's used for.\n"
        "- The 'alt' text must explain what is visible and what is happening.\n"
        "- Avoid special characters or digits in the 'name'.\n"
    )

    if ocr_text:
        prompt += f'\nText in image from OCR:\n"""\n{ocr_text}\n"""\n'

    if detail_level == "minimal":
        prompt += f"\nThe 'name' should be a very short {name_lang} phrase with 1–2 simple words."
    elif detail_level == "normal":
        prompt += f"\nThe 'name' should be a clear {name_lang} phrase with up to 3 words."
    else:
        # default to detailed
        prompt += f"\nThe 'name' should be a descriptive {name_lang} phrase with up to 10 words."

    prompt += f"\nThe 'alt' should be written in {alt_lang}."

    try:
        response = client.responses.create(
            model=MODEL,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": b64_image, "detail": vision_detail}
                ]
            }],
            text={"format": {"type": "json_object"}}
        )

        # Show raw output for debugging
        append_monitor_colored(state, f"[API RAW OUTPUT]\n{response.output_text}", "info")

        # If usage is available, log tokens
        if response.usage:
            used = response.usage.total_tokens
            append_monitor_colored(state, f"[TOKEN USAGE] +{used} tokens", "token")
            prev = state['total_tokens'].get()
            state['total_tokens'].set(prev + used)

        return json.loads(response.output_text)

    except Exception as e:
        append_monitor_colored(state, f"[API ERROR] {e}", "error")
        return None
