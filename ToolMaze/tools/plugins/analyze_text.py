"""
analyze_text Tool Plugin

Function: Analyze text and return statistics
Category: Processor
Domain: General
"""

TOOL_NAME = "analyze_text"


def execute(arguments, context) -> dict:
    """
    Analyze text and return various statistics

    Args:
        arguments: Tool parameters
            - text (str): Text to analyze

    Returns:
        dict: Dictionary containing text analysis results
    """
    text = arguments.get("text")
    if text is None:
        text = ""

    if not isinstance(text, str):
        text = str(text)

    # Basic statistics
    char_count = len(text)
    word_count = len(text.split())
    line_count = text.count('\n') + 1

    # Character type counts
    alpha_count = sum(c.isalpha() for c in text)
    digit_count = sum(c.isdigit() for c in text)
    space_count = sum(c.isspace() for c in text)

    # Find longest word
    words = text.split()
    longest_word = max(words, key=len) if words else ""

    return {
        "raw_content": text,
        "character_count": char_count,
        "word_count": word_count,
        "line_count": line_count,
        "alphabetic_count": alpha_count,
        "digit_count": digit_count,
        "whitespace_count": space_count,
        "longest_word": longest_word,
        "longest_word_length": len(longest_word),
        "average_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0
    }
