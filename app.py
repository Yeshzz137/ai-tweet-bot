# app.py – Streamlit front-end with AUTOMATIC posting + duplication prevention
import streamlit as st
import time
from datetime import datetime
import os
import sys

# ─── Define helpers FIRST ────────────────────────────────────────────────────
POSTED_URLS_FILE = "posted_urls.txt"

def load_posted_urls():
    if not os.path.exists(POSTED_URLS_FILE):
        return set()
    with open(POSTED_URLS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_posted_url(url: str):
    with open(POSTED_URLS_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

# ─── Import your agents ───────────────────────────────────────────────────────
try:
    from search_ai_ml_content import fetch_latest_content
    from summarize_for_tweet import generate_tweet_content
    from post_to_twitter import post_tweet
except ImportError as e:
    print(f"Missing module: {e}")
    if os.getenv("GITHUB_ACTIONS") != "true":
        st.error(f"Missing module: {e}\nMake sure all files are in the same folder.")
        st.stop()
    sys.exit(1)

# ─── NEW: AUTOMATIC TRIGGER FOR GITHUB ACTIONS ───────────────────────────────
# This part runs ONLY on GitHub and ignores all the UI/CSS below it.
if os.getenv("GITHUB_ACTIONS") == "true":
    print("🤖 GitHub Action detected. Running automation...")
    articles = fetch_latest_content(total_limit=10)
    if articles:
        posted_urls = load_posted_urls()
        # Post based on NUM_TWEETS env var (default 1)
        limit = int(os.getenv("NUM_TWEETS", "1"))
        count = 0
        for art in articles:
            if art.get('url') not in posted_urls:
                print(f"Summarizing: {art['title']}")
                tweet_text = generate_tweet_content(art, custom_prompt=os.getenv("CUSTOM_PROMPT", ""))
                if post_tweet(tweet_text):
                    save_posted_url(art['url'])
                    print(f"✅ Posted successfully!")
                    count += 1
                if count >= limit: break
    sys.exit(0) # Stop here so GitHub doesn't try to run Streamlit
# ─────────────────────────────────────────────────────────────────────────────

# ─── Your Original Modern dark SaaS styling ─────────────────────────────
st.set_page_config(
    page_title="AI Tweet Bot • Yeshwath",
    page_icon="🧠🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* Background depth */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #0f172a 0%, #172033 100%) !important;
        }
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
            max-width: 1180px !important;
        }
        h1 {
            font-size: 3.2rem !important;
            background: linear-gradient(90deg, #a78bfa, #c084fc, #f472b6) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            letter-spacing: -1.2px;
            margin-bottom: 0.2rem !important;
        }
        .header-date {
            text-align: right;
            padding-top: 2rem;
            color: #94a3b8;
            font-size: 1rem;
            font-weight: 500;
        }
        section[data-testid="stSidebar"] {
            background: #0f172a !important;
            border-right: 1px solid #334155 !important;
        }
        button[kind="primary"] {
            background: linear-gradient(90deg, #7c3aed, #c084fc) !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 1rem 2.5rem !important;
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            box-shadow: 0 12px 30px rgba(124,58,237,0.45) !important;
            transition: all 0.25s ease !important;
            min-width: 380px !important;
        }
        .card {
            background: rgba(30, 41, 59, 0.85) !important;
            border: 1px solid #475569 !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            margin: 1.4rem 0 !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35) !important;
            backdrop-filter: blur(6px) !important;
        }
    </style>
""", unsafe_allow_html=True)

# Header
col_title, col_date = st.columns([6, 1])
with col_title:
    st.title("🧠 AI Tweet Bot")
with col_date:
    st.markdown(
        f'<div class="header-date">{datetime.now().strftime("%Y-%m-%d %H:%M IST")}</div>',
        unsafe_allow_html=True
    )

st.caption("Fetch fresh AI content → Generate sharp tweets → Auto-post to X (deduplicated)")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    genre = st.selectbox("Content Genre", options=["All Genres", "Research", "Tools", "News"], index=0)
    num_tweets = st.slider("Max tweets this run", 1, 5, 1, 1)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    custom_prompt = st.text_area("Custom Summarization Prompt", height=110, placeholder="Focus on real-world impact...")
    st.markdown('</div>', unsafe_allow_html=True)

# Main CTA
st.markdown('<div style="display: flex; justify-content: center; margin: 2.5rem 0;">', unsafe_allow_html=True)

if st.button("🚀 Fetch → Generate → Auto-Post to X", type="primary"):
    status = st.status("Pipeline running...", expanded=True)
    articles = fetch_latest_content(total_limit=25)
    
    if not articles:
        status.update(label="No articles found", state="error")
        st.stop()

    posted_urls = load_posted_urls()
    new_articles = [a for a in articles if a.get('url') not in posted_urls][:num_tweets]

    if not new_articles:
        status.update(label="No new articles to post", state="complete")
        st.stop()

    for i, article in enumerate(new_articles):
        tweet_text = generate_tweet_content(article, custom_prompt=custom_prompt)
        st.markdown(f'<div class="card"><b>Tweet {i+1}</b><br><code>{tweet_text}</code></div>', unsafe_allow_html=True)
        if post_tweet(tweet_text):
            save_posted_url(article['url'])
            st.success(f"Posted: {article['title']}")
        time.sleep(2)
    
    status.update(label="Pipeline complete!", state="complete")
    st.balloons()

st.markdown('</div>', unsafe_allow_html=True)
