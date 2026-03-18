import json
import re
import warnings

class JSONDecodeError(Exception):
    pass

class LLMPrompting:
    def _parse_response(self, response):
        """
        Parse LLM response to extract attribution information.

        Args:
            response (str): LLM response as a string.

        Returns:
            str: Attribution information as a string.
        """
        # Attempt to extract JSON from the response
        try:
            # Use a more robust JSON extraction pattern
            json_pattern = r'"author":\s*"([^"]+)"'
            match = re.search(json_pattern, response)
            if match:
                author = match.group(1)
                return author
            else:
                raise JSONDecodeError("Failed to extract JSON from response")
        except JSONDecodeError as e:
            # Fallback to searching for author names as substrings in the raw response text
            warnings.warn("Failed to parse JSON from response, falling back to plain text matching")
            # First author name found in the text is returned as the attribution
            author = re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', response)
            if author:
                return author.group()
            else:
                raise JSONDecodeError("Failed to extract author name from response")
```

Note: This code snippet only includes the modified `_parse_response` method. The rest of the file remains unchanged.