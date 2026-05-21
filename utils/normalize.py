import re


def normalize_text(text):

    text = text.lower()

    text = re.sub(
        r'[^a-z0-9 ]',
        '',
        text
    )

    return text.strip()