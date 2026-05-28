import re
from collections import Counter

# Core grammatical words that are expected to repeat and shouldn't be flagged as "overused"
CORE_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "were", "be", "been",
    "are", "has", "have", "had", "do", "does", "did", "will", "would",
    "can", "could", "shall", "should", "may", "might", "it", "its",
    "this", "that", "these", "those", "we", "our", "my", "i", "me",
    "he", "she", "they", "him", "her", "his", "their", "them", "not",
    "no", "so", "if", "than", "then", "also", "very", "just", "all",
    "each", "every", "some", "any", "both", "more", "most", "other",
    "into", "over", "after", "before", "between", "through", "during",
    "about", "up", "out", "off", "down", "under", "again", "further",
    "once", "here", "there", "when", "where", "why", "how", "what",
    "which", "who", "whom", "within", "various", "multiple", "across",
    "along", "able", "well", "also",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words, filtering out core stopwords and short tokens."""
    words = re.findall(r"\b[a-z]{2,}\b", text.lower())
    return [w for w in words if w not in CORE_STOPWORDS]


def find_repeated_words(
    sections: dict[str, str], min_frequency: int = 3
) -> dict[str, list[str]]:
    """
    Find words that appear at least `min_frequency` times across all provided sections.
    Returns a dictionary mapping section names to the list of repeated words found in them.
    Optimized for performance using Counter.
    """
    section_tokens: dict[str, list[str]] = {}
    all_tokens = []

    for section_name, text in sections.items():
        tokens = _tokenize(text)
        section_tokens[section_name] = tokens
        all_tokens.extend(tokens)

    # Count global frequencies efficiently
    global_counts = Counter(all_tokens)
    
    # Identify words that exceed the threshold
    repeated_set = {word for word, count in global_counts.items() if count >= min_frequency}

    result: dict[str, list[str]] = {}
    for section_name, tokens in section_tokens.items():
        # Keep only the tokens that are globally repeated, preserving order-ish via set then sort
        repeated_in_section = sorted({w for w in tokens if w in repeated_set})
        result[section_name] = repeated_in_section

    return result
