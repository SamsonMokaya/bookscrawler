"""
HTML parser for extracting book data from books.toscrape.com
"""
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

from app.utils.helpers import (
    parse_price,
    parse_rating,
    parse_availability,
    normalize_url,
    is_valid_book_url,
    sanitize_text
)

logger = logging.getLogger(__name__)


def parse_book_detail(html: str, url: str) -> Optional[Dict]:
    """
    Parse book detail page and extract all book information
    
    Args:
        html: HTML content of book detail page
        url: URL of the book page
        
    Returns:
        Dictionary with book data or None if parsing fails
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title_elem = soup.select_one('div.product_main h1')
        if not title_elem:
            logger.error(f"Failed to find title for {url}")
            return None
        title = title_elem.text.strip()
        
        # Extract rating
        rating_elem = soup.select_one('p.star-rating')
        rating = parse_rating(rating_elem.get('class', [])) if rating_elem else 0
        
        # Extract description
        description_elem = soup.select_one('#product_description + p')
        description = description_elem.text.strip() if description_elem else ""
        
        # Extract product information table
        table_data = {}
        table = soup.select_one('table.table-striped')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    key = th.text.strip()
                    value = td.text.strip()
                    table_data[key] = value
        
        # Extract prices
        price_excl_tax = parse_price(table_data.get('Price (excl. tax)', '0'))
        price_incl_tax = parse_price(table_data.get('Price (incl. tax)', '0'))
        
        if price_excl_tax is None or price_incl_tax is None:
            logger.error(f"Failed to parse prices for {url}")
            return None
        
        # Extract availability
        availability_str = table_data.get('Availability', 'Out of stock')
        availability, quantity = parse_availability(availability_str)
        
        # Extract number of reviews
        num_reviews_str = table_data.get('Number of reviews', '0')
        try:
            num_reviews = int(num_reviews_str)
        except ValueError:
            num_reviews = 0
        
        # Extract category from breadcrumb
        breadcrumb = soup.select('ul.breadcrumb li')
        category = "Unknown"
        if len(breadcrumb) >= 3:
            # Second to last item is the category
            category_elem = breadcrumb[-2].find('a')
            if category_elem:
                category = category_elem.text.strip()
        
        # Extract image URL
        image_elem = soup.select_one('div.item.active img')
        image_url = ""
        if image_elem:
            image_rel_url = image_elem.get('src', '')
            # Image URL is relative like ../../media/...
            # Need to normalize it
            image_url = normalize_url(image_rel_url, url)
        
        book_data = {
            'name': sanitize_text(title),
            'description': sanitize_text(description),
            'category': category,
            'price_excl_tax': price_excl_tax,
            'price_incl_tax': price_incl_tax,
            'availability': availability,
            'num_reviews': num_reviews,
            'image_url': image_url,
            'rating': rating,
            'source_url': url,
            'raw_html': html[:10000]  # Store first 10KB of HTML
        }
        
        return book_data
        
    except Exception as e:
        logger.error(f"Error parsing book detail page {url}: {e}", exc_info=True)
        return None


def parse_book_list(html: str, page_url: str) -> List[str]:
    """
    Parse catalog page and extract all book URLs
    
    Args:
        html: HTML content of catalog page
        page_url: URL of the catalog page (for normalization)
        
    Returns:
        List of absolute book URLs
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        book_urls = []
        
        # Find all product pods
        products = soup.select('article.product_pod')
        
        for product in products:
            # Find the link to book detail page
            link_elem = product.select_one('h3 a')
            if link_elem:
                rel_url = link_elem.get('href', '')
                if rel_url:
                    # Normalize relative URL to absolute
                    abs_url = normalize_url(rel_url, page_url)
                    if is_valid_book_url(abs_url):
                        book_urls.append(abs_url)
        
        logger.info(f"Found {len(book_urls)} books on page {page_url}")
        return book_urls
        
    except Exception as e:
        logger.error(f"Error parsing book list from {page_url}: {e}", exc_info=True)
        return []


def extract_pagination_info(html: str, current_page_url: str) -> Dict[str, Optional[str]]:
    """
    Extract pagination information from catalog page
    
    Args:
        html: HTML content of catalog page
        current_page_url: URL of current page
        
    Returns:
        Dictionary with 'next', 'previous', 'current_page', 'total_pages'
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        pagination_info = {
            'next': None,
            'previous': None,
            'current_page': 1,
            'total_pages': 1
        }
        
        # Extract current and total pages
        current_elem = soup.select_one('li.current')
        if current_elem:
            # Text like "Page 2 of 50"
            text = current_elem.text.strip()
            parts = text.split()
            if len(parts) >= 4:
                try:
                    pagination_info['current_page'] = int(parts[1])
                    pagination_info['total_pages'] = int(parts[3])
                except ValueError:
                    pass
        
        # Extract next page URL
        next_elem = soup.select_one('li.next a')
        if next_elem:
            next_rel_url = next_elem.get('href', '')
            if next_rel_url:
                pagination_info['next'] = normalize_url(next_rel_url, current_page_url)
        
        # Extract previous page URL
        prev_elem = soup.select_one('li.previous a')
        if prev_elem:
            prev_rel_url = prev_elem.get('href', '')
            if prev_rel_url:
                pagination_info['previous'] = normalize_url(prev_rel_url, current_page_url)
        
        return pagination_info
        
    except Exception as e:
        logger.error(f"Error extracting pagination info: {e}", exc_info=True)
        return {
            'next': None,
            'previous': None,
            'current_page': 1,
            'total_pages': 1
        }
