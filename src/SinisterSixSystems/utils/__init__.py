import re

def sanitze_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
        filename (str): The original filename.
    """
    #remove all special character and replace space with underscore
    sanitized = re.sub(r'[<>:"/\\|?*.,]', '', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:50]