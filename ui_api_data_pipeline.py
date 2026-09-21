import asyncio
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from faker import Faker
import pandas as pd
import requests
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Faker for synthetic test data generation
fake = Faker()


async def fetch_api_data(user_id: int) -> dict:
    """Dependency: requests

    Fetches user context from a REST API to enrich UI automated testing.
    """
    logger.info(f"[API] Fetching metadata for User ID: {user_id}")
    url = f"https://jsonplaceholder.typicode.com/users/{user_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def parse_html_content(html_raw: str) -> str:
    """Dependency: beautifulsoup4

    Parses raw HTML elements extracted from Playwright DOM snapshots.
    """
    soup = BeautifulSoup(html_raw, "html.parser")
    # Clean up whitespace and extra tags
    return soup.get_text(strip=True)


def export_to_excel(data_list: list[dict], output_path: str = "output_report.xlsx"):
    """Dependencies: pandas, openpyxl

    Exports collected test results into a formatted Excel sheet.
    """
    logger.info(f"[Export] Generating Excel report at: {output_path}")
    df = pd.DataFrame(data_list)
    df.to_excel(output_path, index=False, engine="openpyxl")
    logger.info("[Export] Report successfully created!")


async def run_automation():
    collected_results = []

    async with async_playwright() as p:
        logger.info("[Playwright] Launching Chromium Browser...")
        browser = await p.chromium.launch(headless=True, channel="chrome",slow_mo=5000)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Navigate to target site
        logger.info("[Playwright] Navigating to target page...")
        await page.goto("https://quotes.toscrape.com/", wait_until="networkidle")

        # Step 2: Scraping UI elements
        quotes = await page.locator(".quote").all()
        logger.info(f"[Playwright] Found {len(quotes)} quotes on page.")

        for idx, quote in enumerate(quotes[:3], start=1):
            # Extract UI text using Playwright
            quote_text = await quote.locator(".text").inner_text()
            author_text = await quote.locator(".author").inner_text()

            # Extract raw HTML snippet and clean with BeautifulSoup
            raw_html = await quote.inner_html()
            cleaned_text = parse_html_content(raw_html)

            # Step 3: Enrich with API Data (requests)
            api_user = await fetch_api_data(idx)

            # Step 4: Generate Synthetic Metadata (Faker)
            test_run_id = fake.uuid4()
            executor_email = fake.company_email()

            # Consolidate record
            record = {
                "Test_Run_ID": test_run_id,
                "Executor_Email": executor_email,
                "Quote_Author": author_text,
                "Quote_Text": quote_text,
                "Parsed_Clean_HTML": cleaned_text[:50] + "...",  # Truncated
                "API_Assigned_User": api_user.get("name"),
                "API_User_Company": api_user.get("company", {}).get("name"),
            }
            collected_results.append(record)

        await browser.close()
        logger.info("[Playwright] Browser session closed.")

    # Step 5: Export dataset (pandas + openpyxl)
    export_to_excel(collected_results)


if __name__ == "__main__":
    asyncio.run(run_automation())