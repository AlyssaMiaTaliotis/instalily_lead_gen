try:
    from backend.scrapers.company_scraper import enrich_contacts_with_linkedin
    print("OK: Import worked!")
except Exception as e:
    print("IMPORT FAILED:", e)