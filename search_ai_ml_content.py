# search_ai_ml_content.py
# Fetches latest articles from multiple RSS feeds focused on AI, ML, data science & tech news

import feedparser
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from datetime import datetime

# ────────────────────────────────────────────────
# List of RSS feeds – easy to add/remove/edit
# ────────────────────────────────────────────────
RSS_SOURCES = [
    {
        "name": "Towards Data Science",
        "url": "https://towardsdatascience.com/feed/",
        "category": "Tutorials & Articles",
        "max_entries": 4,
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "Open Source AI & Models",
        "max_entries": 3,
    },
    {
        "name": "Google Research Blog",
        "url": "https://research.google/blog/rss/",
        "category": "Research & Breakthroughs",
        "max_entries": 2,
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss/",
        "category": "Frontier AI & Announcements",
        "max_entries": 2,
    },
    {
        "name": "arXiv – cs.LG (Machine Learning)",
        "url": "https://arxiv.org/rss/cs.LG",
        "category": "Latest Papers",
        "max_entries": 5,
    },
    {
        "name": "TechCrunch – AI",
        "url": "https://techcrunch.com/tag/artificial-intelligence/feed/",
        "category": "Industry & Startups",
        "max_entries": 3,
    },
    {
        "name": "KDnuggets",
        "url": "https://www.kdnuggets.com/feed",
        "category": "Data Science Roundup",
        "max_entries": 3,
    },
    # Add more here, e.g.:
    # {
    #     "name": "DeepMind Blog",
    #     "url": "https://deepmind.google/discover/blog/rss/",
    #     "category": "Research",
    #     "max_entries": 2,
    # },
]

def clean_description(text: Optional[str]) -> str:
    """Remove HTML, boilerplate, and common RSS junk from description/summary."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(" ", strip=True)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove typical teaser endings and meta phrases
    junk_patterns = [
        r'(Read more|Continue reading|…|\[…\]).*$',
        r'(appeared first on|posted on|published in|from Towards Data Science|Medium).*$',
        r'(Image by author|Image by Author).*',
        r'^\s*Why you shouldn\'t.*',  # common TDS opener
    ]
    for pat in junk_patterns:
        text = re.sub(pat, '', text, flags=re.I).strip()
    
    return text

def fetch_latest_content(
    total_limit: int = 12,
    min_description_length: int = 40
) -> List[Dict]:
    """
    Fetches recent articles from all configured RSS feeds.
    
    Returns:
        List of dicts sorted by recency (newest first)
    """
    all_articles = []

    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            
            if feed.bozo:
                print(f"⚠️  Parse warning for {source['name']}: {feed.bozo_exception}")
            
            entries = feed.entries[:source.get("max_entries", 5)]
            fetched_count = 0

            for entry in entries:
                # Get description/summary/content
                desc_raw = (
                    getattr(entry, 'summary', None)
                    or getattr(entry, 'content', [{}])[0].get('value', '')
                    or entry.get('description', '')
                    or entry.title
                )
                
                cleaned_desc = clean_description(desc_raw)
                
                # Skip very short / useless entries
                if len(cleaned_desc) < min_description_length and "paper" not in entry.title.lower():
                    continue

                article = {
                    "title": (entry.title or "Untitled").strip(),
                    "url": entry.link,
                    "description": cleaned_desc,
                    "source": source["name"],
                    "category": source["category"],
                    "published": entry.get('published_parsed') or entry.get('updated_parsed'),
                    "published_str": entry.get('published', ''),
                }
                
                all_articles.append(article)
                fetched_count += 1

            print(f"✓ {fetched_count} articles from {source['name']}")

        except Exception as e:
            print(f"❌ Failed to fetch {source['name']}: {e}")

    # Sort by published date (newest first), fallback to insertion order
    all_articles.sort(
        key=lambda x: x["published"] if x["published"] else datetime.min.timetuple(),
        reverse=True
    )

    return all_articles[:total_limit]


# ────────────────────────────────────────────────
# Quick test when running directly
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching latest AI/ML/tech content from multiple sources...\n")
    
    articles = fetch_latest_content(total_limit=15)
    
    if not articles:
        print("No articles found. Check internet connection or feed URLs.")
    else:
        print(f"Found {len(articles)} recent articles:\n")
        for i, art in enumerate(articles, 1):
            print(f"[{i}] {art['source']}  •  {art['category']}")
            print(f"    {art['title']}")
            print(f"    {art['url']}")
            desc_snip = art['description'][:180].replace('\n', ' ')
            print(f"    {desc_snip}{'...' if len(art['description']) > 180 else ''}")
            if art['published_str']:
                print(f"    Published: {art['published_str']}")
            print()