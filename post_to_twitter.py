# post_to_twitter.py

import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

# Use Tweepy Client (v2 API)
client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
)

def post_tweet(tweet_text):
    try:
        response = client.create_tweet(text=tweet_text)
        print("✅ Tweet posted:", response.data)
        return True
    except tweepy.TweepyException as e:
        print("❌ Failed to post tweet:", e)
        return False