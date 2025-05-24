"""
ai_handler.py

Communicates with OpenAI's GPT-4.1-nano for image description.
- Optionally includes OCR text in the prompt if enabled
- Returns 'name' and 'alt' in a structured JSON
- Logs usage tokens (if available) and accumulates them in state['total_tokens']
"""

from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError, BadRequestError 
import json
from .helpers import image_to_base64, extract_text_from_image

# MODEL = "gpt-4.1-nano" # Commented out as per instructions

def describe_image(logger, state, image_path: str) -> dict | None:
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
            logger.error(ocr_result)
            ocr_text = ""
        else:
            logger.warn(f"[OCR RESULT] {ocr_result}")
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
        model_name_from_state = state.get('ai_model', 'gpt-4.1-nano') # Default if not in state
        logger.info(f"Using AI Model: {model_name_from_state}") # Log the model being used
        response = client.responses.create( # Changed from client.chat.completions.create
            model=model_name_from_state,
            input=[{ # Assuming this is the correct structure for gpt-4.1-nano image input
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": b64_image, "detail": vision_detail}
                ]
            }],
            text={"format": {"type": "json_object"}} # Changed from response_format
        )

        # Log raw output for debugging (if logger has a debug level)
        if hasattr(logger, 'debug'):
            logger.debug(f"[API RAW OUTPUT]\n{response.output_text}")
        else:
            logger.info(f"[API RAW OUTPUT - First 100 chars]\n{response.output_text[:100]}")


        if response.usage:
            used = response.usage.total_tokens
            logger.token(f"+{used} tokens") # Assuming logger has a 'token' method
            
            # Update total_tokens in state (ensure state['total_tokens'] is an int)
            # In the PyQt app, state['total_tokens'] is passed as an int initially (0)
            # and is managed directly as an int within logic.py context.
            # Here, we ensure it's handled correctly if it were to be modified directly in ai_handler.
            if 'total_tokens' not in state or not isinstance(state['total_tokens'], int):
                state['total_tokens'] = 0 # Initialize if not present or wrong type
            state['total_tokens'] += used

        return json.loads(response.output_text)

    except AuthenticationError as e:
        logger.error(f"[API Auth Error] Please check your OpenAI API key. Details: {e}")
        return None
    except RateLimitError as e:
        logger.error(f"[API Rate Limit Error] You have exceeded your current quota or rate limit. Details: {e}")
        return None
    except APIConnectionError as e:
        logger.error(f"[API Connection Error] Could not connect to OpenAI. Check your network. Details: {e}")
        return None
    except BadRequestError as e: # Often due to invalid request structure or model parameters
        logger.error(f"[API Bad Request Error] The request to OpenAI was invalid (e.g., bad model name, malformed input). Details: {e}")
        return None
    except APIError as e: # More generic OpenAI API error
        logger.error(f"[OpenAI API Error] An API error occurred. Details: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"[API Response JSON Error] Failed to parse JSON from model response. Details: {e}. Response text: {response.output_text if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"[Unexpected API Handler Error] An unexpected error occurred: {e}")
        return None
