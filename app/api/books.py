"""
Books API endpoints
"""
from fastapi import APIRouter, Query, HTTPException, status, Path
from typing import Optional
import logging
import math

from app.models import Book
from app.api.schemas import BookResponse, BooksListResponse
from app.api.dependencies import APIKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=BooksListResponse)
async def get_books(
    api_key: APIKey,
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating (1-5)"),
    availability: Optional[str] = Query(None, description="Filter by availability status"),
    search: Optional[str] = Query(None, description="Search in book name/description"),
    sort_by: Optional[str] = Query("name", description="Sort field (price_incl_tax, rating, num_reviews, name, crawled_at)"),
    order: Optional[str] = Query("asc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page (max 100)")
):
    """
    Get list of books with filters and pagination
    
    **Filters:**
    - `category`: Filter by book category (e.g., "Poetry", "Fiction")
    - `min_price`: Minimum price (inclusive)
    - `max_price`: Maximum price (inclusive)
    - `rating`: Filter by rating (1-5 stars)
    - `availability`: Filter by availability status
    - `search`: Search in book name and description
    
    **Sorting:**
    - `sort_by`: Field to sort by (price_incl_tax, rating, num_reviews, name, crawled_at)
    - `order`: Sort order (asc or desc)
    
    **Pagination:**
    - `page`: Page number (starts at 1)
    - `limit`: Number of results per page (1-100)
    """
    try:
        # Build query filter
        query_filter = {}
        
        if category:
            query_filter['category'] = {"$regex": category, "$options": "i"}  # Case-insensitive
        
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter['$gte'] = min_price
            if max_price is not None:
                price_filter['$lte'] = max_price
            query_filter['price_incl_tax'] = price_filter
        
        if rating is not None:
            query_filter['rating'] = rating
        
        if availability:
            query_filter['availability'] = {"$regex": availability, "$options": "i"}
        
        if search:
            # Search in name and description
            query_filter['$or'] = [
                {'name': {"$regex": search, "$options": "i"}},
                {'description': {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total = await Book.find(query_filter).count()
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = math.ceil(total / limit) if total > 0 else 1
        
        # Determine sort order
        sort_order = 1 if order == "asc" else -1
        
        # Validate sort_by field
        valid_sort_fields = ['name', 'price_incl_tax', 'rating', 'num_reviews', 'crawled_at', 'updated_at', 'category']
        if sort_by not in valid_sort_fields:
            sort_by = 'name'
        
        # Build sort string
        sort_str = f"{'+' if sort_order == 1 else '-'}{sort_by}"
        
        # Execute query with pagination
        books = await Book.find(query_filter).sort(sort_str).skip(skip).limit(limit).to_list()
        
        # Convert to response model
        book_responses = [
            BookResponse(
                id=str(book.id),
                name=book.name,
                description=book.description,
                category=book.category,
                price_excl_tax=book.price_excl_tax,
                price_incl_tax=book.price_incl_tax,
                availability=book.availability,
                num_reviews=book.num_reviews,
                rating=book.rating,
                image_url=str(book.image_url),
                source_url=str(book.source_url),
                crawled_at=book.crawled_at,
                updated_at=book.updated_at
            )
            for book in books
        ]
        
        logger.info(f"Returned {len(book_responses)} books (page {page}/{total_pages})")
        
        return BooksListResponse(
            total=total,
            page=page,
            limit=limit,
            pages=total_pages,
            books=book_responses
        )
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch books"
        )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str = Path(..., description="Book ID"),
    api_key: APIKey = None
):
    """
    Get a single book by ID
    
    **Path Parameters:**
    - `book_id`: The unique identifier of the book
    
    **Returns:**
    - Book details including all fields
    
    **Errors:**
    - 404: Book not found
    """
    try:
        # Find book by ID
        book = await Book.get(book_id)
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with ID '{book_id}' not found"
            )
        
        logger.info(f"Returned book: {book.name}")
        
        return BookResponse(
            id=str(book.id),
            name=book.name,
            description=book.description,
            category=book.category,
            price_excl_tax=book.price_excl_tax,
            price_incl_tax=book.price_incl_tax,
            availability=book.availability,
            num_reviews=book.num_reviews,
            rating=book.rating,
            image_url=str(book.image_url),
            source_url=str(book.source_url),
            crawled_at=book.crawled_at,
            updated_at=book.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch book"
        )
