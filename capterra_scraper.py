import time
import re
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scraper_base import ReviewScraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class CapterraScraper(ReviewScraper):
    def fetch_reviews(self, company_name: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        reviews = []
        print(f"[{self.__class__.__name__}] Starting search for {company_name}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            try:
                # Step 1: Search for the company
                search_url = f"https://www.capterra.com/search-results/?search={company_name}"
                page.goto(search_url, timeout=60000)
                page.wait_for_load_state("networkidle")

                # Parse search results
                # Selectors for search results might vary. 
                # Usually: .search-result a (with href containing /p/)
                # Let's try to find the first link that looks like a product page /p/
                
                # Wait for results to load
                try:
                    page.wait_for_selector('a[href*="/p/"]', timeout=10000)
                except:
                    print(f"No results found for {company_name} on Capterra.")
                    return []

                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                product_link = None
                for a in soup.find_all('a', href=True):
                    if '/p/' in a['href']:
                        product_link = a['href']
                        break
                
                if not product_link:
                    print(f"Could not identify product link for {company_name}")
                    return []
                
                full_product_url = urljoin("https://www.capterra.com", product_link)
                # Ensure we are at reviews or go to reviews
                # Capterra URL: /p/ID/Slug/
                # Reviews are usually lower down or we can try appending "reviews/" if acceptable, 
                # but standard Capterra is single page app often.
                # Actually, capturing the reviews might require clicking "Reviews" tab if it exists.
                
                print(f"Found product page: {full_product_url}")
                page.goto(full_product_url, timeout=60000)
                page.wait_for_load_state("networkidle")
                
                # Clicking "Reviews" if it's a tab or scrolling down.
                # Check for "Reviews" in text to click or verify presence.
                # Actually, some Capterra pages have /reviews/ suffix valid. Let's try navigating there directly?
                # Format: https://www.capterra.com/p/123/Product/reviews/ ??
                # Let's try constructing it.
                if not full_product_url.endswith('/'):
                    full_product_url += '/'
                reviews_url = f"{full_product_url}reviews/"
                
                print(f"Navigating to reviews page: {reviews_url}")
                response = page.goto(reviews_url)
                
                # If 404 or redirect back to product page, then maybe the single page view is used.
                if response.status == 404 or page.url != reviews_url:
                    print("Direct reviews link failed, using product page...")
                    page.goto(full_product_url)
                    # Scroll to reviews or click "Read all reviews"
                    # This part is highly dynamic. For this assignment, we will attempt to find review cards.

                page.wait_for_load_state("networkidle")
                
                # Expand all reviews if possible? Or pagination?
                # Capterra uses "Show more" usually.
                
                collected_count = 0
                while True:
                    # Parse reviews
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    review_cards = soup.select('.review-card') or soup.select('[data-testid="review-card"]')
                    
                    print(f"Found {len(review_cards)} reviews visible.")
                    
                    new_reviews_found = False
                    
                    for card in review_cards:
                        try:
                            # Extract Title
                            title_el = card.select_one('h3') or card.select_one('.review-card-title')
                            title = title_el.get_text(strip=True) if title_el else "No Title"
                            
                            # Extract Body
                            # Might be split into Pros/Cons or General
                            body_text = []
                            comments = card.select('.review-comments-text')
                            for c in comments:
                                body_text.append(c.get_text(strip=True))
                            
                            description = "\n".join(body_text) if body_text else ""
                            if not description:
                                # Fallback
                                body_el = card.select_one('.review-text') 
                                description = body_el.get_text(strip=True) if body_el else ""

                            # Extract Date
                            # "Written on Oct 12, 2023" or similar
                            date_el = card.select_one('.review-date') or card.select_one('[data-testid="review-date"]')
                            date_str_raw = date_el.get_text(strip=True) if date_el else ""
                            
                            # Clean "Written on "
                            date_str = date_str_raw.replace("Written on", "").strip()
                            
                            review_date = None
                            if date_str:
                                try:
                                    # Format: October 12, 2023
                                    review_date = datetime.strptime(date_str, "%B %d, %Y")
                                except:
                                    try:
                                        # Format: 12/10/2023
                                        review_date = datetime.strptime(date_str, "%d/%m/%Y")
                                    except:
                                        pass
                            
                            # Deduplicate by looking up if we already have this review title+date+desc? 
                            # Capterra "Show more" appends to list usually.
                            
                            review_obj = {
                                "source": "Capterra",
                                "title": title,
                                "description": description,
                                "date": date_str,
                                "rating": None
                            }
                            review_obj['_dt'] = review_date

                            # Check date range
                            if review_date:
                                if start_date <= review_date <= end_date:
                                    # unique check simple
                                    if review_obj not in reviews:
                                        reviews.append(review_obj)
                                        new_reviews_found = True
                            else:
                                if review_obj not in reviews:
                                     reviews.append(review_obj) # Add anyway if date parse fails

                        except Exception as e:
                            # print(f"Error parsing capterra review: {e}")
                            continue

                    # Pagination / Show More
                    # Capterra usually has a "Show more" button
                    show_more_btn = page.query_selector('button:has-text("Show more")')
                    if show_more_btn and show_more_btn.is_visible():
                        try:
                            show_more_btn.click()
                            time.sleep(2) # Wait for ajax
                            if not new_reviews_found and len(review_cards) > 50: 
                                # If we didn't add new reviews (maybe date range passed) and we have a lot, maybe stop?
                                # But we can't be sure they are ordered by date.
                                pass
                        except:
                            break
                    else:
                        break
                    
                    # Safety break
                    if len(reviews) > 200: 
                        break

            except Exception as e:
                print(f"An error occurred during Capterra scraping: {e}")
            finally:
                browser.close()
        
        return reviews
