import os
import re
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

OUT_DIR = Path("knowledge/raw") / datetime.date.today().isoformat()


def slugify(text: str, max_len: int = 60) -> str:
    text = text[:max_len].lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text


def save_result(idx: int, result: dict) -> None:
    slug = slugify(result['title'])
    filename = f"{idx:02d}-{slug}.md"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    scraped_at = datetime.date.today().isoformat()
    front_matter = (
        f'---\n'
        f'title: "{result["title"]}"\n'
        f'url: "{result["url"]}"\n'
        f'scraped_at: "{scraped_at}"\n'
        f'---\n\n'
    )
    path.write_text(front_matter + result['markdown'])
    print(f"Saved: {path}")


if __name__ == "__main__":
    api_key = os.getenv("FIRECRAWL_API_KEY")

    api_url = "https://api.firecrawl.dev/v2/search"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "query": "Chipotle investor relations press releases",
        "limit": 5,
        "scrapeOptions": {"formats": ["markdown"]}
    }

    response = requests.post(api_url, headers=headers, json=payload)

    data = response.json()
    results = data["data"]["web"]
    print(f"Firecrawl returned {len(results)} results")

    for idx, r in enumerate(results, start=1):
        title = r.get('title', '')
        url = r.get('url', '')
        if not r.get('markdown'):
            print(f'WARNING: no markdown for "{title}" ({url}) — skipping')
            continue
        save_result(idx, r)
