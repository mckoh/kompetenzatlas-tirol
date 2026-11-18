def clean_text(text:str) -> str:
    """Cleans a text removing multiple spaces.

    :param text: The uncleaned text
    :type text: str
    :returns: Cleaned text
    :rtype: str
    """
    return " ".join(text.split())
