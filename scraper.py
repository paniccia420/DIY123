"""
DIY Help App — Content Pipeline Scraper
Pulls tutorials from YouTube + blogs for a given category/subcategory,
dedupes against existing URLs, and writes into Postgres (schema.sql).

Env vars required:
    DATABASE_URL       - postgres connection string
    YOUTUBE_API_KEY     - Google Cloud YouTube Data API v3 key
"""

import os
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

DATABASE_URL = os.environ["DATABASE_URL"]
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]

SEARCH_PLAN = {
    "home-improvement": [
        "how to fix a leaky faucet",
        "how to patch drywall",
        "how to install a ceiling fan",
    ],
    "auto-mechanics": [
        "how to change brake pads",
        "how to jump start a car",
        "how to change engine oil",
    ],
}

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"


def get_db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_or_create_category(cur, slug):
    cur.execute("SELECT id FROM categories WHERE slug = %s", (slug,))
    row = cur.fetchone()
    if row:
        return row["id"]
    name = slug.replace("-", " ").title()
    cur.execute(
        "INSERT INTO categories (name, slug) VALUES (%s, %s) RETURNING id",
        (name, slug),
    )
    return cur.fetchone()["id"]


def get_or_create_source(cur, source_type, domain, trust_score=0.5):
    cur.execute(
        "SELECT id FROM sources WHERE type = %s AND domain = %s",
        (source_type, domain),
    )
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute(
        "INSERT INTO sources (type, domain, trust_score) VALUES (%s, %s, %s) RETURNING id",
        (source_type, domain, trust_score),
    )
    return cur.fetchone()["id"]


def search_youtube(query, max_results=5):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "relevanceLanguage": "en",
        "videoDuration": "medium",
    }
    resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("items", [])


def get_video_details(video_ids):
    params = {
        "part": "contentDetails,snippet",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }
    resp = requests.get(YOUTUBE_VIDEO_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("items", [])


def parse_iso8601_duration(duration):
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return None
    h, m, s = (int(x) if x else 0 for x in match.groups())
    return h * 3600 + m * 60 + s


def scrape_youtube_for_query(cur, category_id, query):
    source_id = get_or_create_source(cur, "youtube", "youtube.com", trust_score=0.6)

    results = search_youtube(query)
    video_ids = [item["id"]["videoId"] for item in results if "videoId" in item.get("id", {})]
    if not video_ids:
        return 0

    details = get_video_details(video_ids)
    inserted = 0

    for video in details:
        vid = video["id"]
        url = f"https://www.youtube.com/watch?v={vid}"
        title = video["snippet"]["title"]
        description = video["snippet"].get("description", "")
        duration = parse_iso8601_duration(video["contentDetails"]["duration"])

        cur.execute("SELECT id FROM tutorials WHERE url = %s", (url,))
        if cur.fetchone():
            continue

        cur.execute(
            """
            INSERT INTO tutorials
                (source_id, category_id, title, url, content_type,
                 raw_text, duration_seconds)
            VALUES (%s, %s, %s, %s, 'video', %s, %s)
            """,
            (source_id, category_id, title, url, description, duration),
        )
        inserted += 1

    return inserted


def run():
    conn = get_db_conn()
    cur = conn.cursor()
    total_inserted = 0

    for category_slug, queries in SEARCH_PLAN.items():
        category_id = get_or_create_category(cur, category_slug)

        for query in queries:
            try:
                n = scrape_youtube_for_query(cur, category_id, query)
                total_inserted += n
                print(f"[{category_slug}] '{query}' -> {n} new videos")
            except Exception as e:
                print(f"Error scraping YouTube for '{query}': {e}")

            conn.commit()
            time.sleep(1)

    cur.close()
    conn.close()
    print(f"Done. {total_inserted} new tutorials inserted at {datetime.now(timezone.utc)}")


if __name__ == "__main__":
    run()
