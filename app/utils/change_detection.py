"""
Change detection utilities for tracking book updates
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging

from app.models import Book, ChangeLog
from app.utils.helpers import TRACKED_FIELDS

logger = logging.getLogger(__name__)


async def detect_changes(old_book: Book, new_book_data: Dict) -> List[Dict]:
    """
    Detect changes between existing book and new scraped data
    
    Args:
        old_book: Existing Book document from database
        new_book_data: Newly scraped book data dictionary
        
    Returns:
        List of change dictionaries to create ChangeLog entries
    """
    changes = []
    
    for field in TRACKED_FIELDS:
        old_value = getattr(old_book, field, None)
        new_value = new_book_data.get(field)
        
        # Skip if values are the same
        if old_value == new_value:
            continue
        
        # Create change record
        change = {
            'book_id': str(old_book.id),  # Convert ObjectId to string
            'book_name': old_book.name,
            'changed_at': datetime.utcnow(),
            'change_type': 'update',
            'field_changed': field,
            'old_value': old_value,
            'new_value': new_value,
            'description': _generate_change_description(field, old_value, new_value)
        }
        
        changes.append(change)
        logger.info(f"Change detected in '{old_book.name}': {field} changed from {old_value} to {new_value}")
    
    return changes


async def save_changes_to_log(changes: List[Dict]) -> int:
    """
    Save detected changes to ChangeLog collection
    
    Args:
        changes: List of change dictionaries
        session: Optional MongoDB session for transactions
        
    Returns:
        Number of changes saved
    """
    if not changes:
        return 0
    
    try:
        # Create ChangeLog documents
        changelogs = [ChangeLog(**change) for change in changes]
        
        # Bulk insert
        await ChangeLog.insert_many(changelogs)
        
        logger.info(f"Saved {len(changelogs)} changes to ChangeLog")
        return len(changelogs)
        
    except Exception as e:
        logger.error(f"Error saving changes to log: {e}", exc_info=True)
        return 0


def _generate_change_description(field: str, old_value, new_value) -> str:
    """
    Generate human-readable description of change
    
    Args:
        field: Field name that changed
        old_value: Old value
        new_value: New value
        
    Returns:
        Human-readable description
    """
    if field == 'price_incl_tax':
        if new_value > old_value:
            diff = new_value - old_value
            return f"Price increased by £{diff:.2f} (from £{old_value:.2f} to £{new_value:.2f})"
        else:
            diff = old_value - new_value
            return f"Price decreased by £{diff:.2f} (from £{old_value:.2f} to £{new_value:.2f})"
    
    elif field == 'price_excl_tax':
        if new_value > old_value:
            diff = new_value - old_value
            return f"Price (excl. tax) increased by £{diff:.2f}"
        else:
            diff = old_value - new_value
            return f"Price (excl. tax) decreased by £{diff:.2f}"
    
    elif field == 'availability':
        return f"Availability changed from '{old_value}' to '{new_value}'"
    
    elif field == 'num_reviews':
        diff = new_value - old_value
        if diff > 0:
            return f"Number of reviews increased by {diff} (now {new_value})"
        else:
            return f"Number of reviews decreased by {abs(diff)} (now {new_value})"
    
    elif field == 'rating':
        if new_value > old_value:
            return f"Rating improved from {old_value} to {new_value} stars"
        else:
            return f"Rating decreased from {old_value} to {new_value} stars"
    
    elif field == 'category':
        return f"Category changed from '{old_value}' to '{new_value}'"
    
    else:
        return f"{field} changed from '{old_value}' to '{new_value}'"


async def get_recent_changes(
    limit: int = 50,
    change_type: Optional[str] = None,
    book_id: Optional[str] = None
) -> List[ChangeLog]:
    """
    Get recent changes from ChangeLog
    
    Args:
        limit: Maximum number of changes to return
        change_type: Filter by change type (e.g., 'update', 'new_book')
        book_id: Filter by specific book ID
        
    Returns:
        List of ChangeLog documents
    """
    query = {}
    
    if change_type:
        query['change_type'] = change_type
    
    if book_id:
        query['book_id'] = book_id
    
    changes = await ChangeLog.find(query).sort('-changed_at').limit(limit).to_list()
    return changes


async def get_book_change_history(book_id: str) -> List[ChangeLog]:
    """
    Get complete change history for a specific book
    
    Args:
        book_id: Book ID
        
    Returns:
        List of all changes for this book, sorted by date (newest first)
    """
    changes = await ChangeLog.find(
        ChangeLog.book_id == book_id
    ).sort('-changed_at').to_list()
    
    return changes

