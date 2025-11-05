"""
Pydantic schemas for API responses
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    """Response schema for a single book"""
    id: str = Field(..., description="Book ID")
    name: str
    description: Optional[str] = None
    category: str
    price_excl_tax: float
    price_incl_tax: float
    availability: str
    num_reviews: int
    rating: int
    image_url: str
    source_url: str
    crawled_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "690b24fb9d8ccb72dea4ecfb",
                "name": "A Light in the Attic",
                "description": "A classic collection of poetry...",
                "category": "Poetry",
                "price_excl_tax": 51.77,
                "price_incl_tax": 51.77,
                "availability": "In stock",
                "num_reviews": 0,
                "rating": 3,
                "image_url": "https://books.toscrape.com/media/...",
                "source_url": "https://books.toscrape.com/catalogue/...",
                "crawled_at": "2025-11-05T10:20:41",
                "updated_at": "2025-11-05T10:20:41"
            }
        }


class BooksListResponse(BaseModel):
    """Response schema for paginated books list"""
    total: int = Field(..., description="Total number of books")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    pages: int = Field(..., description="Total number of pages")
    books: List[BookResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 1000,
                "page": 1,
                "limit": 20,
                "pages": 50,
                "books": []
            }
        }


class ChangeResponse(BaseModel):
    """Response schema for a single change log entry"""
    id: str = Field(..., description="Change log ID")
    book_id: str
    book_name: str
    change_type: str
    field_changed: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    changed_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "690b24fb9d8ccb72dea4ed00",
                "book_id": "690b24fb9d8ccb72dea4ecfb",
                "book_name": "A Light in the Attic",
                "change_type": "update",
                "field_changed": "price_incl_tax",
                "old_value": 99.99,
                "new_value": 51.77,
                "changed_at": "2025-11-05T10:33:24"
            }
        }


class ChangesListResponse(BaseModel):
    """Response schema for paginated changes list"""
    total: int = Field(..., description="Total number of changes")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    pages: int = Field(..., description="Total number of pages")
    changes: List[ChangeResponse]


class BookHistoryResponse(BaseModel):
    """Response schema for book-specific change history"""
    book_id: str
    book_name: str
    total_changes: int
    changes: List[ChangeResponse]


class StatsResponse(BaseModel):
    """Response schema for statistics"""
    total_books: int
    last_crawl: Optional[datetime] = None
    total_changes_today: int
    categories: dict
    price_range: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_books": 1000,
                "last_crawl": "2025-11-05T10:30:46",
                "total_changes_today": 25,
                "categories": {"Poetry": 150, "Fiction": 200},
                "price_range": {"min": 10.00, "max": 99.99, "avg": 45.50}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid or missing API key"
            }
        }

