"""
ChangeLog Beanie model for MongoDB

Tracks all changes to book records for audit trail and change reports
"""

from beanie import Document, Indexed, Link
from datetime import datetime
from typing import Any, Optional
from pydantic import Field
from bson import ObjectId


class ChangeLog(Document):
    """
    Change log document model
    
    Records all changes to book data (price changes, availability, etc.)
    """
    
    # Reference to the book that changed
    book_id: Indexed(str)  # Book ObjectId as string (indexed for fast lookup)
    book_name: str  # Book name (for easy reference)
    
    # Change information
    changed_at: Indexed(datetime) = Field(default_factory=datetime.utcnow)  # When change occurred
    field_changed: Optional[str] = None  # Which field changed (e.g., 'price_incl_tax', 'availability')
    
    # Old and new values
    old_value: Optional[Any] = None  # Previous value
    new_value: Optional[Any] = None  # New value
    
    # Change classification
    change_type: Indexed(str)  # 'update', 'new_book', 'deleted'
    
    # Optional: Additional information
    description: Optional[str] = None  # Human-readable description of the change
    source_url: Optional[str] = None  # URL of the book
    
    class Settings:
        name = "changelogs"  # MongoDB collection name
        
        # Indexes for efficient querying
        indexes = [
            "book_id",  # Find all changes for a specific book
            "changed_at",  # Sort by date
            "change_type",  # Filter by type
            [("changed_at", -1)],  # Descending order for recent changes
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "book_id": "507f1f77bcf86cd799439011",
                "book_name": "A Light in the Attic",
                "changed_at": "2025-11-05T10:00:00",
                "field_changed": "price_incl_tax",
                "old_value": 51.77,
                "new_value": 45.99,
                "change_type": "update",
                "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
            }
        }
