import re
import string
import logging

logger = logging.getLogger(__name__)

class TextNormalizer:
    """Text normalization utilities for TTS."""
    
    @staticmethod
    def clean_text_for_tts(text: str) -> str:
        """Clean and normalize text for TTS generation."""
        if not text or not text.strip():
            return ""
        
        # Remove voice instructions in square brackets
        text = re.sub(r'\[.*?\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Handle common abbreviations
        abbreviations = {
            'Mr.': 'Mister',
            'Mrs.': 'Missus', 
            'Dr.': 'Doctor',
            'Prof.': 'Professor',
            'Ltd.': 'Limited',
            'Inc.': 'Incorporated',
            'Corp.': 'Corporation',
            'Co.': 'Company',
            'vs.': 'versus',
            'etc.': 'etcetera',
            'i.e.': 'that is',
            'e.g.': 'for example',
        }
        
        for abbrev, expansion in abbreviations.items():
            text = text.replace(abbrev, expansion)
        
        # Handle numbers (basic)
        text = re.sub(r'\b(\d+)\b', lambda m: num_to_words(int(m.group(1))), text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{2,}', '...', text)
        
        # Ensure proper sentence endings
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    @staticmethod
    def split_into_sentences(text: str, max_length: int = 200) -> List[str]:
        """Split text into sentences with length limits."""
        if not text:
            return []
        
        # Basic sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Split long sentences
        result = []
        for sentence in sentences:
            if len(sentence) <= max_length:
                result.append(sentence)
            else:
                # Split on commas or other punctuation
                parts = re.split(r'[,;:]+', sentence)
                current = ""
                for part in parts:
                    part = part.strip()
                    if len(current + part) <= max_length:
                        current = current + ", " + part if current else part
                    else:
                        if current:
                            result.append(current)
                        current = part
                if current:
                    result.append(current)
        
        return result

def num_to_words(num: int) -> str:
    """Convert number to words (basic implementation)."""
    if num == 0:
        return "zero"
    
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", 
             "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    if num < 10:
        return ones[num]
    elif num < 20:
        return teens[num - 10]
    elif num < 100:
        return tens[num // 10] + ("" if num % 10 == 0 else " " + ones[num % 10])
    elif num < 1000:
        return ones[num // 100] + " hundred" + ("" if num % 100 == 0 else " " + num_to_words(num % 100))
    else:
        return str(num)  # Fallback for large numbers

def clean_text_for_tts(text: str) -> str:
    """Legacy function for compatibility."""
    return TextNormalizer.clean_text_for_tts(text)
