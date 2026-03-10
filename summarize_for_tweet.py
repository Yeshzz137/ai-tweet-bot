# summarize_for_tweet.py

import os
import re
from transformers import pipeline

# Prevent heavy backends
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["TRANSFORMERS_NO_JAX"] = "1"  # fixed typo
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # CPU only

# Load summarizer
summarizer = None
try:
    summarizer = pipeline(
        "text2text-generation",
        model="t5-small",
        tokenizer="t5-small",
        framework="pt",
        device=-1  # CPU
    )
    print("✅ t5-small summarizer loaded successfully")
except Exception as e:
    print(f"❌ Failed to load t5-small: {e}")
    summarizer = None

def clean_description(text: str) -> str:
    """Basic cleaning for RSS descriptions"""
    if not text:
        return ""
    # Remove common teaser junk
    text = re.sub(r'(Read more|Continue reading|…Read more|Image by author).*', '', text, flags=re.I)
    text = re.sub(r'https?://\S+', '', text)  # remove URLs
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_tweet_content(article_info: dict, custom_prompt: str = "") -> str:
    """
    Generates tweet-ready text from article dict.
    Now supports optional custom_prompt to guide summarization.
    """
    title = article_info.get('title', 'AI/ML News').strip()
    raw_content = article_info.get('description', '')
    url = article_info.get('url', '#')
    source = article_info.get('source', '').strip()

    content = clean_description(raw_content)

    # Prepare input for T5
    if len(content) < 80:
        print("Short content → using title boost")
        input_text = f"summarize: {title}. {content}"
    else:
        input_text = "summarize: " + content

    # Add custom prompt if provided (this is the key change)
    if custom_prompt.strip():
        input_text = f"summarize: {custom_prompt}. {input_text}"

    input_text = input_text.strip()[:750]  # safe input limit

    # Generate summary
    summary = ""
    if summarizer:
        try:
            summary_result = summarizer(
                input_text,
                max_length=80,
                min_length=30,
                do_sample=False,
                num_beams=5,               # better quality
                repetition_penalty=1.2,    # reduce title/meta repeats
                early_stopping=True
            )
            summary = summary_result[0]['summary_text'].strip()
            # Clean T5 artifacts
            summary = re.sub(r'^\.\s*', '', summary)
            summary = summary.capitalize()
            print(f"✅ Summary: {summary}")
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            summary = ""

    # Fallback chain
    if not summary or len(summary) < 30:
        print("Weak summary → fallback")
        if len(content) >= 60:
            summary = content[:180].rstrip() + "..."
        else:
            summary = title[:140] + "…" if len(title) > 90 else title

    # Build tweet
    tweet = f"🧠 {title}"
    if source:
        tweet += f" ({source})"
    tweet += f"\n\n{summary}\n\n🔗 {url}"

    # Trim to 280 chars
    if len(tweet) > 280:
        available = 280 - len(f"🧠 {title[:120]}…\n\n…\n\n🔗 {url}") - 10
        if available > 40:
            summary_trim = summary[:available - 3].rstrip() + "..."
            tweet = f"🧠 {title}\n\n{summary_trim}\n\n🔗 {url}"
        else:
            tweet = f"🧠 {title[:160]}…\n🔗 {url}"

    return tweet[:280]

# ────────────────────────────────────────────────
# Testing block (unchanged)
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print("--- Testing generate_tweet_content ---")
    # ... your existing test cases ...
