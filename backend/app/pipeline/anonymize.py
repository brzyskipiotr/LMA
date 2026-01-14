"""
Pseudo-anonymization for PII before sending to external APIs.
Supports Polish and English patterns.
"""
import re

# Polish patterns
PESEL_PATTERN = re.compile(r'\b\d{11}\b')  # Polish national ID
NIP_PATTERN = re.compile(r'\b\d{10}\b')  # Polish tax ID
REGON_PATTERN = re.compile(r'\b\d{9}\b')  # Polish business registry

# Universal patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,3}\)?[-.\s]?\d{3}[-.\s]?\d{3,4}\b')
IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,6}\d{0,4}\b')

# Name patterns (simplified - catches common formats)
# Polish: "Jan Kowalski", "KOWALSKI JAN"
# English: "John Smith", "SMITH JOHN"
NAME_PATTERN = re.compile(
    r'\b(?:'
    # First Last (capitalized)
    r'[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+|'
    # LAST FIRST (uppercase)
    r'[A-ZĄĆĘŁŃÓŚŹŻ]{2,}\s+[A-ZĄĆĘŁŃÓŚŹŻ]{2,}'
    r')\b'
)

# Address patterns (street + number, keep city for geocoding)
# Polish: "ul. Warszawska 15", "al. Jerozolimskie 100/5"
# English: "123 Main Street", "45 Oak Ave"
STREET_NUMBER_PATTERN = re.compile(
    r'\b(?:'
    # Polish: ul./al./pl. + name + number
    r'(?:ul\.|al\.|pl\.|os\.)\s*[A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż\s]+\s+\d+[a-zA-Z]?(?:/\d+)?|'
    # English: number + street name
    r'\d+\s+[A-Za-z]+\s+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Drive|Dr\.?|Lane|Ln\.?|Boulevard|Blvd\.?)'
    r')\b',
    re.IGNORECASE
)

# Postal codes
POSTAL_CODE_PL = re.compile(r'\b\d{2}-\d{3}\b')  # Polish: 00-000
POSTAL_CODE_INTL = re.compile(r'\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b')  # UK format


def anonymize_text(text: str) -> str:
    """
    Replace PII with placeholders.
    Keeps location names (cities) for geocoding purposes.
    """
    result = text

    # Replace in order of specificity (most specific first)
    result = EMAIL_PATTERN.sub('[EMAIL]', result)
    result = IBAN_PATTERN.sub('[IBAN]', result)
    result = PESEL_PATTERN.sub('[PESEL]', result)
    result = NIP_PATTERN.sub('[NIP]', result)
    result = REGON_PATTERN.sub('[REGON]', result)
    result = PHONE_PATTERN.sub('[PHONE]', result)
    result = POSTAL_CODE_PL.sub('[POSTAL]', result)
    result = POSTAL_CODE_INTL.sub('[POSTAL]', result)

    # Names - be careful not to replace company names or locations
    # Only replace if it looks like a person name (2 words, both capitalized)
    result = NAME_PATTERN.sub('[NAME]', result)

    # Street addresses (but keep city names)
    result = STREET_NUMBER_PATTERN.sub('[ADDRESS]', result)

    return result


def anonymize_pages(pages: list[str]) -> list[str]:
    """Anonymize multiple pages of text."""
    return [anonymize_text(page) for page in pages]
