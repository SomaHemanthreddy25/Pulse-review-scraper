import time
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scraper_base import ReviewScraper
from bs4 import BeautifulSoup

class TrustRadiusScraper(ReviewScraper):
    def fetch_reviews(self, company_name: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        reviews = []
        # TrustRadius URL structure: https://www.trustradius.com/products/{slug}/reviews
        slug = company_name.lower().replace(' ', '-')
        url = f"https://www.trustradius.com/products/{slug}/reviews"
        
        print(f"[{self.__class__.__name__}] Starting scrape for {company_name} from {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=60000)
                page.wait_for_load_state("networkidle")
                
                if page.status_code == 404:
                    print(f"Product page not found for {company_name}")
                    return []

                # TrustRadius has a long scroll or pagination.
                
                while True:
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Select review articles
                    review_elements = soup.select('article.review-card') 
                    if not review_elements:
                        review_elements = soup.select('.serp-review')

                    print(f"Found {len(review_elements)} reviews on this page.")
                    
                    for el in review_elements:
                        try:
                            # Title
                            title_el = el.select_one('h3') or el.select_one('.review-title section')
                            title = title_el.get_text(strip=True) if title_el else "No Title"
                            
                            # Body
                            body_el = el.select_one('.review-content') or el.select_one('.response-text')
                            body = body_el.get_text(strip=True) if body_el else ""
                            
                            # Date
                            # "Written March 12, 2023"
                            date_el = el.select_one('.review-date')
                            date_str_raw = date_el.get_text(strip=True) if date_el and date_el.get_text(strip=True) else ""
                            
                            date_str = date_str_raw.replace("Written", "").strip() or date_str_raw.strip()
                            
                            review_date = None
                            if date_str:
                                try:
                                    review_date = datetime.strptime(date_str, "%B %d, %Y")
                                except:
                                    pass
                            
                            review_obj = {
                                "source": "TrustRadius",
                                "title": title,
                                "description": body,
                                "date": date_str,
                                "rating": None
                            }
                            review_obj['_dt'] = review_date
                            
                            if review_date:
                                if start_date <= review_date <= end_date:
                                    reviews.append(review_obj)
                            else:
                                reviews.append(review_obj)

                        except Exception as e:
                            continue
                    
                    # Next Page
                    next_button = page.query_selector('a.next-page') or page.query_selector('button[aria-label="Next"]')
                    if next_button and next_button.is_visible() and next_button.is_enabled():
                        next_button.click()
                        time.sleep(2)
                        page.wait_for_load_state("networkidle")
                    else:
                        break
            
            except Exception as e:
                print(f"An error occurred during TrustRadius scraping: {e}")
            finally:
                browser.close()

        return reviews
