import praw
import json
import time
from tqdm import tqdm
import datetime
import os

from datetime import datetime as dt

# 1. Reddit API credentials
client_id = 'wQEuOcq3Oxz8EJaf1hzigg'
client_secret = 'Walqn1Xz7h20dbvppmTcv16Fxl7uhg'
user_agent = 'sury-umanch'

# 2. Connect to Reddit
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent
)

# 3. Config
SUBREDDIT_NAME = "ukpolitics"
KEYWORDS = ['"universal income"', '"minimum wage"', '"council tax"', '"income tax"', '"national insurance"', '"poverty"']
LIMIT = 50

# 4. Media detection helpers
media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.webm', '.avi', '.flv', '.wmv', '.mkv']
media_sources = ['youtube.com', 'youtu.be', 'imgur.com', 'v.redd.it']

def check_media_in_text(text):
    text = text.lower()
    return any(ext in text for ext in media_extensions + media_sources) or "http" in text

def check_post_media(submission):
    return (
        submission.is_video or
        any(submission.url.lower().endswith(ext) for ext in media_extensions) or
        any(source in submission.url.lower() for source in media_sources) or
        hasattr(submission, 'preview') or
        submission.media is not None
    )

# 5. Recursive function to get nested replies
def get_replies(comment):
    if isinstance(comment, praw.models.MoreComments):
        return []  # Avoid getting a 'MoreComments' object, which is not a real comment
    replies = []
    for reply in comment.replies:
        replies.append({
            'url': f"https://www.reddit.com{reply.permalink}",
            'date': dt.fromtimestamp(reply.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
            'reply_id': reply.id,
            'votes': reply.score,
            "body": reply.body,
            "has_multimedia": check_media_in_text(reply.body),
            "replies": get_replies(reply)
        })
    return replies

# 6. Collect data
structured_data = {
    keyword.strip('\"'): [] for keyword in KEYWORDS
}
subreddit = reddit.subreddit(SUBREDDIT_NAME)

for keyword in KEYWORDS:
    posts = list(subreddit.search(f'title:{keyword}', sort="new", limit=LIMIT))
    print(f"🔍 Found {len(posts)} posts for the keyword: {keyword}. Starting extraction...")

    for submission in tqdm(posts, desc="Extracting posts", unit="post"):
        submission.comments.replace_more(limit=None)

        post_data = {
            'url': f"https://www.reddit.com{submission.permalink}",
            'date': dt.fromtimestamp(submission.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
            'id': submission.id,
            'votes': submission.score,
            "title": submission.title,
            "has_multimedia": check_post_media(submission),
            "comments": []
        }

        for top_comment in submission.comments:
            post_data["comments"].append({
                'url': f"https://www.reddit.com{top_comment.permalink}",
                'date': dt.fromtimestamp(top_comment.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                'comment_id': top_comment.id,
                'votes': top_comment.score,
                "body": top_comment.body,
                "has_multimedia": check_media_in_text(top_comment.body),
                "replies": get_replies(top_comment)
            })

        structured_data[keyword.strip('\"')].append(post_data)
        time.sleep(1)

# 7. Save to JSON
os.makedirs("data", exist_ok=True)
file_path = os.path.join(f"data/{SUBREDDIT_NAME}_data.json")
if os.path.exists(file_path):
    i = 1
    while os.path.exists(os.path.join('data', f"{SUBREDDIT_NAME}_{i}.json")):
        i += 1
    file_path = os.path.join('data', f"{SUBREDDIT_NAME}_{i}.json")

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(structured_data, f, ensure_ascii=False, indent=2)

print(f"✅ Data saved to {file_path}")

# 8. Metrics Function
def count_all_replies(comments):
    total = 0
    for comment in comments:
        total += 1  # Count the comment itself
        total += count_all_replies(comment.get("replies", []))  # Recursively count replies
    return total
