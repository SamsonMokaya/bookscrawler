"""
Book Beanie model for MongoDB

Represents a book from books.toscrape.com with all required fields
"""

from beanie import Document, Indexed
from datetime import datetime
from typing import Optional
from pydantic import Field, HttpUrl
import hashlib


class Book(Document):
    """
    Book document model
    
    All fields from books.toscrape.com plus metadata for tracking
    """
    
    # Required book information
    name: Indexed(str)  # Book title (indexed for search)
    description: Optional[str] = None  # Book description (can be missing)
    category: Indexed(str)  # Book category (indexed for filtering)
    
    # Pricing information
    price_excl_tax: float = Field(ge=0)  # Price excluding tax (must be >= 0)
    price_incl_tax: float = Field(ge=0)  # Price including tax (must be >= 0)
    
    # Availability and reviews
    availability: str  # e.g., "In stock (22 available)"
    num_reviews: int = Field(ge=0, default=0)  # Number of reviews
    
    # Media
    image_url: str  # URL to book cover image
    
    # Rating (1-5 stars)
    rating: int = Field(ge=1, le=5)  # 1 to 5 stars
    
    # Metadata (for tracking and change detection)
    source_url: Indexed(str, unique=True)  # Original URL (unique - prevents duplicates)
    crawled_at: datetime = Field(default_factory=datetime.utcnow)  # When we scraped it
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # Last update time
    crawl_status: str = Field(default="success")  # success, error, pending
    
    # Raw HTML snapshot (fallback)
    raw_html: Optional[str] = None  # Store original HTML
    
    # Content hash for change detection
    content_hash: str  # Hash of key fields to detect changes
    
    class Settings:
        name = "books"  # MongoDB collection name
        
        # Indexes for efficient querying
        indexes = [
            "name",  # Search by name
            "category",  # Filter by category
            "rating",  # Filter/sort by rating
            "price_incl_tax",  # Filter/sort by price
            [("source_url", 1)],  # Unique index on source_url
        ]
    
    @staticmethod
    def generate_content_hash(name: str, price_incl_tax: float, availability: str) -> str:
        """
        Generate hash of key fields for change detection
        
        Args:
            name: Book name
            price_incl_tax: Price including tax
            availability: Availability status
            
        Returns:
            SHA256 hash string
        """
        content = f"{name}|{price_incl_tax}|{availability}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def update_hash(self):
        """Update the content hash based on current field values"""
        self.content_hash = self.generate_content_hash(
            self.name,
            self.price_incl_tax,
            self.availability
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "A Light in the Attic",
                "description": "It's hard to imagine a world without A Light in the Attic...",
                "category": "Poetry",
                "price_excl_tax": 51.77,
                "price_incl_tax": 51.77,
                "availability": "In stock (22 available)",
                "num_reviews": 0,
                "image_url": "http://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
                "rating": 3,
                "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "crawl_status": "success"
            }
        }
