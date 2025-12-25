import argparse
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any

from g2_scraper import G2Scraper
from capterra_scraper import CapterraScraper
from trustradius_scraper import TrustRadiusScraper

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def main():
    parser = argparse.ArgumentParser(description="Scrape product reviews from G2, Capterra, and TrustRadius.")
    
    parser.add_argument("--company", required=True, help="Name of the company/product to scrape reviews for.")
    parser.add_argument("--start_date", required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end_date", required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument("--source", required=True, choices=["g2", "capterra", "trustradius", "all"], 
                        help="Source to scrape from. Use 'all' for all sources.")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode.")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run browser in visible mode (debug).")

    args = parser.parse_args()

    # Validate Dates
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format.")
        return

    if start_date > end_date:
        print("Error: Start date cannot be after end date.")
        return

    print(f"Scraping reviews for '{args.company}' from {start_date.date()} to {end_date.date()}...")

    scrapers = []
    if args.source == "g2" or args.source == "all":
        scrapers.append(G2Scraper(headless=args.headless))
    if args.source == "capterra" or args.source == "all":
        scrapers.append(CapterraScraper(headless=args.headless))
    if args.source == "trustradius" or args.source == "all":
        scrapers.append(TrustRadiusScraper(headless=args.headless))

    all_reviews = []

    for scraper in scrapers:
        try:
            reviews = scraper.fetch_reviews(args.company, start_date, end_date)
            # Filter just in case scraper returned extra
            filtered = scraper.filter_reviews_by_date(reviews, start_date, end_date)
            # Remove internal keys for clean output
            for r in filtered:
                if '_dt' in r:
                    del r['_dt']
            all_reviews.extend(filtered)
            print(f"Collected {len(filtered)} reviews from {scraper.__class__.__name__}.")
        except Exception as e:
            print(f"Failed to scrape using {scraper.__class__.__name__}: {e}")
            traceback.print_exc()

    # Output JSON
    output_filename = f"{args.company}_reviews.json"
    with open(output_filename, "w", encoding='utf-8') as f:
        json.dump(all_reviews, f, default=json_serial, indent=4)

    print(f"\nSuccess! Saved {len(all_reviews)} reviews to {output_filename}")

if __name__ == "__main__":
    main()
