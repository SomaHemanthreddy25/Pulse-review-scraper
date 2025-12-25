import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scraper_base import ReviewScraper
from bs4 import BeautifulSoup

class G2Scraper(ReviewScraper):
    def fetch_reviews(self, company_name: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        reviews = []
        # G2 generic URL structure: https://www.g2.com/products/{company_name}/reviews
        # Note: company_name needs to be the slug.
        url = f"https://www.g2.com/products/{company_name.lower().replace(' ', '-')}/reviews"
        
        print(f"[{self.__class__.__name__}] Starting scrape for {company_name} from {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=60000)
                # Handle potential Cloudflare/Bot checks by waiting a bit or checking title
                page.wait_for_load_state("networkidle")

                if "Just a moment" in page.title():
                    print("Detected Cloudflare challenge. Waiting...")
                    time.sleep(10)
                
                # Check if page exists
                if page.status_code == 404:
                    print(f"Product page not found for {company_name}")
                    return []

                # G2 uses infinite scroll or pagination. Usually pagination for reviews.
                # Inspecting G2 structure (simulated): Reviews are often in containers like .paper or [itemprop="review"]
                
                # Loop for pagination
                while True:
                    # Parse current page
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # This selector is an approximation based on common G2 structures
                    review_elements = soup.select('div[itemprop="review"]')
                    
                    if not review_elements:
                         # Fallback for different layouts
                        review_elements = soup.select('.review-id')

                    print(f"Found {len(review_elements)} reviews on this page.")
                    
                    page_new_reviews = False
                    
                    for el in review_elements:
                        try:
                            # Extract Title
                            title_el = el.select_one('[itemprop="name"]') or el.select_one('.review-list-heading')
                            title = title_el.get_text(strip=True) if title_el else "No Title"
                            
                            # Extract Body
                            body_el = el.select_one('[itemprop="reviewBody"]') or el.select_one('.formatted-text')
                            body = body_el.get_text(strip=True) if body_el else ""
                            
                            # Extract Date
                            # Date formatting on G2 can vary, e.g., "Oct 12, 2023"
                            date_el = el.select_one('[itemprop="datePublished"]') or el.select_one('.time')
                            date_str = date_el.get_text(strip=True) if date_el and date_el.get_text(strip=True) else None
                            
                            # Try to find meta content for date if available
                            if date_el and date_el.has_attr('content'):
                                date_str = date_el['content']

                            review_date = None
                            if date_str:
                                try:
                                    # Attempt multiple formats
                                    for fmt in ["%b %d, %Y", "%Y-%m-%d", "%B %d, %Y"]:
                                        try:
                                            review_date = datetime.strptime(date_str, fmt)
                                            break
                                        except ValueError:
                                            continue
                                except Exception:
                                    pass
                            
                            if review_date:
                                # Optimization: Stop if we hit reviews older than start_date?
                                # G2 usually sorts by default relevance or date. If date, we can break.
                                # Assuming mixed, we just collect.
                                pass

                            review = {
                                "source": "G2",
                                "title": title,
                                "description": body,
                                "date": date_str,  # Keep original string for reference
                                "rating": None # Could extract rating meta
                            }
                            
                            # Add normalized date object for filtering
                            review['_dt'] = review_date

                            # Filter logical check here or at end. prefer at end but for optimization checking date:
                            if review_date:
                                if start_date <= review_date <= end_date:
                                    reviews.append(review)
                                    page_new_reviews = True
                            else:
                                # If no date found, we might skip or include with warning. 
                                # For this assignment, lets include and filter later if we can't parse
                                pass

                        except Exception as e:
                            print(f"Error parsing a review: {e}")
                            continue

                    # Pagination Check
                    # Look for "Next" button
                    next_button = page.query_selector('.pagination__named-link.next') or page.query_selector('a.next_page')
                    
                    if next_button and next_button.is_visible() and next_button.is_enabled():
                        # Optional: check if we have collected enough based on date (if sorted)
                        # For safety, just click next
                        try:
                            next_button.click()
                            page.wait_for_load_state("networkidle")
                            time.sleep(2) # Polite wait
                        except Exception as e:
                            print(f"Error navigating to next page: {e}")
                            break
                    else:
                        break

            except Exception as e:
                print(f"An error occurred during G2 scraping: {e}")
            finally:
                browser.close()
        
        return reviews
