# app.py – Streamlit front-end with AUTOMATIC posting + duplication prevention
import streamlit as st
import time
from datetime import datetime
import os

# Import your agents
try:
    from search_ai_ml_content import fetch_latest_content
    from summarize_for_tweet import generate_tweet_content
    from post_to_twitter import post_tweet
except ImportError as e:
    st.error(f"Missing module: {e}\nMake sure all files are in the same folder.")
    st.stop()

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

# ─── Modern dark SaaS styling – enhanced version ─────────────────────────────
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

        /* Title – bigger + gradient */
        h1 {
            font-size: 3.2rem !important;
            background: linear-gradient(90deg, #a78bfa, #c084fc, #f472b6) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            letter-spacing: -1.2px;
            margin-bottom: 0.2rem !important;
        }

        /* Header date */
        .header-date {
            text-align: right;
            padding-top: 2rem;
            color: #94a3b8;
            font-size: 1rem;
            font-weight: 500;
        }

        /* Sidebar polish */
        section[data-testid="stSidebar"] {
            background: #0f172a !important;
            border-right: 1px solid #334155 !important;
        }
        .sidebar .stSelectbox > div > div,
        .sidebar .stSlider > div,
        .sidebar .stTextArea > div > div {
            background: #1e293b !important;
            border: 1px solid #475569 !important;
            border-radius: 10px !important;
            transition: all 0.2s ease !important;
        }
        .sidebar .stSelectbox > div > div:hover,
        .sidebar .stSlider:hover,
        .sidebar .stTextArea:hover {
            border-color: #a78bfa !important;
            box-shadow: 0 0 12px rgba(167,139,250,0.2) !important;
        }

        /* Big centered CTA button */
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
        button[kind="primary"]:hover {
            transform: translateY(-4px) scale(1.03) !important;
            box-shadow: 0 18px 40px rgba(124,58,237,0.6) !important;
        }

        /* Consistent cards */
        .card {
            background: rgba(30, 41, 59, 0.85) !important;
            border: 1px solid #475569 !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            margin: 1.4rem 0 !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35) !important;
            backdrop-filter: blur(6px) !important;
            transition: transform 0.2s, box-shadow 0.2s !important;
        }
        .card:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 14px 40px rgba(0,0,0,0.45) !important;
        }

        /* Code / tweet text */
        pre {
            border-radius: 12px !important;
            background: #0f172a !important;
            border: 1px solid #334155 !important;
            padding: 1.2rem !important;
        }

        /* Status boxes */
        .stAlert, .stSuccess, .stInfo, .stStatus {
            border-radius: 12px !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="AI Tweet Bot • Yeshwath",
    page_icon="🧠🚀",  # changed to brain + rocket – looks much better
    layout="wide",
    initial_sidebar_state="expanded"
)

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

    genre = st.selectbox(
        "Content Genre",
        options=[
            "All Genres",
            "Research Papers & Breakthroughs",
            "Open Source Models & Tools",
            "Industry News & Startups",
            "Tutorials & Practical Guides",
            "Ethical AI & Societal Impact"
        ],
        index=0
    )

    num_tweets = st.slider(
        "Max tweets this run",
        1, 5, 1, 1
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    custom_prompt = st.text_area(
        "Custom Summarization Prompt (optional)",
        height=110,
        placeholder="Examples:\n• Focus on real-world applications & impact\n• Highlight benchmarks/numbers\n• Keep tone engaging yet professional"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.info(
        "Tweets are only posted if the URL is new (checked against posted_urls.txt)\nDuplicates skipped automatically."
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Main CTA – centered
st.markdown('<div style="display: flex; justify-content: center; margin: 2.5rem 0;">', unsafe_allow_html=True)

if st.button("🚀 Fetch → Generate → Auto-Post to X", type="primary"):
    status = st.status("Pipeline running...", expanded=True)
    progress = st.progress(0)

    status.update(label="Fetching latest articles...", state="running")
    articles = fetch_latest_content(total_limit=25)
    if not articles:
        status.update(label="Failed to fetch articles", state="error")
        st.error("No content available.")
        st.stop()
    progress.progress(0.25)
    status.update(label=f"Fetched {len(articles)} articles", state="complete")

    status.update(label="Checking for new/unposted articles...", state="running")
    posted_urls = load_posted_urls()  # ← now defined
    new_articles = []
    skipped = []
    for art in articles:
        url = art.get('url', '')
        if url and url in posted_urls:
            skipped.append(art)
        else:
            new_articles.append(art)
        if len(new_articles) >= num_tweets * 2:
            break
    progress.progress(0.5)

    if not new_articles:
        status.update(label="No new articles to post (all recent ones already posted)", state="complete")
        if skipped:
            with st.expander("Already posted articles (skipped)"):
                for s in skipped[:5]:
                    st.caption(f"{s['source']} • {s['title'][:60]}... → {s['url']}")
        st.stop()

    status.update(label=f"Found {len(new_articles)} new articles → preparing up to {num_tweets} tweets", state="complete")

    posted_success = 0
    for i, article in enumerate(new_articles[:num_tweets]):
        status.update(label=f"Generating & posting tweet {i+1}/{min(num_tweets, len(new_articles))}", state="running")
        try:
            tweet_text = generate_tweet_content(
                article,
                custom_prompt=custom_prompt.strip()
            )

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"**Tweet {i+1} prepared**")
            st.code(tweet_text, language=None)
            st.caption(f"{article.get('source', 'Source')} • {article['title'][:90]}{'...' if len(article['title']) > 90 else ''}")
            st.markdown('</div>', unsafe_allow_html=True)

            if post_tweet(tweet_text):
                posted_success += 1
                save_posted_url(article['url'])
                st.success(f"Tweet {i+1} posted successfully! URL saved.")
            else:
                st.warning(f"Tweet {i+1} failed to post – check API/console")
            time.sleep(5)
        except Exception as e:
            st.error(f"Error on tweet {i+1}: {e}")

        progress.progress(0.5 + (i + 1) / (num_tweets * 2))

    progress.progress(1.0)

    if posted_success > 0:
        status.update(label=f"Success! {posted_success} new tweet(s) posted to X", state="complete", expanded=True)
        st.balloons()
    else:
        status.update(label="Pipeline finished – no new tweets posted", state="error", expanded=True)

    if skipped:
        with st.expander("Skipped (already posted earlier)"):
            for s in skipped[:8]:
                st.caption(f"{s['source']} • {s['title'][:70]}... → {s['url']}")

st.markdown('</div>', unsafe_allow_html=True)