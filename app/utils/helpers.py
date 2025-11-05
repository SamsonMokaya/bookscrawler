"""
Utility helper functions for the book scraper
"""
import hashlib
import re
from typing import Optional
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


# Fields to track for change detection
TRACKED_FIELDS = [
    'price_excl_tax',
    'price_incl_tax',
    'availability',
    'num_reviews',
    'rating',
    'category'
]


def generate_content_hash(book_data: dict, fields: list = None) -> str:
    """
    Generate a hash of book content for change detection
    
    Args:
        book_data: Dictionary with book data
        fields: List of fields to include in hash (defaults to TRACKED_FIELDS)
        
    Returns:
        SHA256 hash string
    """
    if fields is None:
        fields = TRACKED_FIELDS
    
    # Build content string from specified fields
    content_parts = []
    for field in sorted(fields):  # Sort for consistency
        value = book_data.get(field, '')
        content_parts.append(f"{field}:{value}")
    
    content = "|".join(content_parts)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string to float
    
    Args:
        price_str: Price string like "£51.77" or "51.77"
        
    Returns:
        Float price or None if parsing fails
    """
    try:
        # Remove currency symbols and extract number
        cleaned = re.sub(r'[£$€,]', '', price_str.strip())
        return float(cleaned)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse price '{price_str}': {e}")
        return None


def parse_rating(rating_class: str) -> int:
    """
    Parse rating from CSS class name
    
    Args:
        rating_class: CSS class like "star-rating Three"
        
    Returns:
        Rating as integer (1-5), defaults to 0 if parsing fails
    """
    rating_map = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    
    for word, rating in rating_map.items():
        if word in rating_class:
            return rating
    
    logger.warning(f"Failed to parse rating from class '{rating_class}'")
    return 0


def parse_availability(availability_str: str) -> tuple[str, int]:
    """
    Parse availability string
    
    Args:
        availability_str: String like "In stock (22 available)" or "In stock"
        
    Returns:
        Tuple of (status, quantity)
        Example: ("In stock", 22)
    """
    # Extract number in parentheses
    match = re.search(r'\((\d+)\s+available\)', availability_str)
    quantity = int(match.group(1)) if match else 0
    
    # Get status (everything before the parentheses or full string)
    status = re.sub(r'\s*\(.*\)', '', availability_str).strip()
    
    return status, quantity


def normalize_url(url: str, base_url: str = "https://books.toscrape.com") -> str:
    """
    Normalize relative URL to absolute URL
    
    Args:
        url: Relative or absolute URL
        base_url: Base URL to join with
        
    Returns:
        Absolute URL
    """
    return urljoin(base_url, url)


def is_valid_book_url(url: str) -> bool:
    """
    Check if URL is a valid book detail page
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid book URL
    """
    return 'catalogue/' in url and '/index.html' in url and '_' in url


def extract_book_id(url: str) -> Optional[str]:
    """
    Extract book ID from URL
    
    Args:
        url: Book URL like "catalogue/a-light-in-the-attic_1000/index.html"
        
    Returns:
        Book ID like "1000" or None
    """
    match = re.search(r'_(\d+)/index\.html', url)
    return match.group(1) if match else None


def sanitize_text(text: Optional[str]) -> str:
    """
    Clean and sanitize text content
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep basic punctuation
    cleaned = re.sub(r'[^\w\s.,!?\-\'\"]+', '', cleaned)
    
    return cleaned
