import json
import re
import logging

# Define the expected JSON schema for LLM responses
LLM_RESPONSE_SCHEMA = {
    "author": str,
    "text": str,
}


def _parse_response(response):
    """
    Parse the LLM response and extract the author attribution.

    This function uses a more robust JSON extraction pattern and adds validation
    that extracted JSON keys match the expected schema.

    Args:
        response (str): The raw LLM response text.

    Returns:
        str: The author attribution extracted from the response.
    """
    # Attempt to extract JSON from the response using a regex pattern
    json_pattern = r'"author":\s*"([^"]*)"\s*}'
    match = re.search(json_pattern, response)
    if match:
        # Extract the author name from the match
        author = match.group(1)
        try:
            # Validate that the extracted JSON keys match the expected schema
            json_response = json.loads(response)
            if set(LLM_RESPONSE_SCHEMA.keys()) == set(json_response.keys()):
                return author
            else:
                logging.warning("Invalid JSON response format")
                return None
        except json.JSONDecodeError:
            # If JSON decoding fails, log a warning and return None
            logging.warning("Failed to parse JSON response")
            return None
    else:
        # If no JSON match is found, log a warning and return None
        logging.warning("No JSON match found in response")
        return None
