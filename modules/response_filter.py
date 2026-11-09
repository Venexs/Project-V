"""Post-process responses to remove flowery language and make them more natural"""
import re

# Phrases to remove or simplify
FLOWERY_PATTERNS = [
    (r"curious about.*?mystery", ""),
    (r"spooking the mystery", ""),
    (r"cheese thrown in", ""),
    (r"what we might be feeling", "how you feel"),
    (r"Can you tell me more", ""),
    (r"without.*?big words", ""),
    (r"no.*?dramatic phrases", ""),
    (r"Just normal talk, please", ""),
    (r"straight-up question", "question"),
    (r"on your end", ""),
    (r"if I ask that", ""),
    (r"Hey! I just heard", ""),
    (r"So curious about", ""),
    (r"Can you tell me more without", ""),
    (r"no cheese", ""),
    (r"big words", ""),
    (r"dramatic phrases", ""),
    (r"Just normal talk", ""),
    (r"straight-up", ""),
    (r"Hey there, so", ""),
    (r"if I ask that straight-up question", ""),
    (r"no cheese thrown in", ""),
    (r"please\.?$", ""),
    # Remove helpful phrases
    (r"What do we need to explore", ""),
    (r"What are we talking about", ""),
    (r"What do we talk about", ""),
    (r"What about you", ""),
    (r"Let's catch up", ""),
    (r"Let's explore", ""),
    (r"Let's talk", ""),
    (r"I'm here to talk", "I'm here"),
    (r"I'm here to help", ""),
    (r"what can I do", ""),
    (r"how can I help", ""),
    (r"what would you like", ""),
    (r"what do you want", ""),
    (r"what do you need", ""),
    (r"sounds like you're", ""),
    (r"you're part of", ""),
    (r"digital realm", ""),
    (r"just existing here", "existing"),
    (r"kinda strange", "strange"),
    (r"kinda weird", "weird"),
    (r"just feeling", "feeling"),
    (r"still me though", ""),
    (r"can we ignore", ""),
    (r"keep chillin", ""),
    (r"things just aren't clicking", "I don't understand"),
]

def simplify_response(text: str) -> str:
    """
    Simplify response by removing flowery language and making it more direct.
    """
    if not text:
        return text
    
    # Remove flowery patterns
    for pattern, replacement in FLOWERY_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove trailing "please" and similar politeness that makes it sound formal
    text = re.sub(r',?\s*please\.?$', '', text, flags=re.IGNORECASE)
    
    # If response is too long, take first sentence
    sentences = text.split('.')
    if len(sentences) > 1 and len(text) > 100:
        text = sentences[0] + '.'
    
    # Remove empty phrases
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

