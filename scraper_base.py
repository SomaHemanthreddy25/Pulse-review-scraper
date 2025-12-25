from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any

class ReviewScraper(ABC):
    def __init__(self, headless: bool = True):
        self.headless = headless

    @abstractmethod
    def fetch_reviews(self, company_name: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetches reviews for the given company within the specified date range.
        
        Args:
            company_name: Name of the company/product.
            start_date: Start date for the reviews.
            end_date: End date for the reviews.
            
        Returns:
            A list of dictionaries, where each dictionary represents a review.
        """
        pass

    def filter_reviews_by_date(self, reviews: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Helper method to filter a list of reviews by date.
        Assumes each review has a 'date' field as a datetime object or parseable string.
        """
        filtered = []
        for review in reviews:
            review_date = review.get('date')
            if isinstance(review_date, str):
                # Try parsing if it's a string, this might need customization per source if formats vary wildly
                pass 
            
            if review_date and start_date <= review_date <= end_date:
                filtered.append(review)
        return filtered
