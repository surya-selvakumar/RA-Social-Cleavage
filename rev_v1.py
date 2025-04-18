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
LIMIT = 10

# 4. Media and link detection helpers
media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.webm', '.avi', '.flv', '.wmv', '.mkv']
media_sources = ['youtube.com', 'youtu.be', 'imgur.com', 'v.redd.it']

def check_media_in_text(text):
    text = text.lower()
    return any(ext in text for ext in media_extensions + media_sources)

def check_links_in_text(text):
    text = text.lower()
    return "http" in text or "www." in text

def check_post_media(submission):
    return (
        submission.is_video or
        any(submission.url.lower().endswith(ext) for ext in media_extensions) or
        any(source in submission.url.lower() for source in media_sources) or
        hasattr(submission, 'preview') or
        submission.media is not None
    )

def check_post_links(submission):
    return "http" in submission.url or "www." in submission.url

# 5. Recursive function to get nested replies
def get_replies(comment):
    if isinstance(comment, praw.models.MoreComments):
        return []
    replies = []
    for reply in comment.replies:
        body_text = reply.body
        replies.append({
            'url': f"https://www.reddit.com{reply.permalink}",
            'date': dt.fromtimestamp(reply.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
            'reply_id': reply.id,
            'votes': reply.score,
            "body": body_text,
            "has_multimedia": check_media_in_text(body_text),
            "has_links": check_links_in_text(body_text),
            "replies": get_replies(reply)
        })
    return replies

# 6. Collect data
structured_data = {
    keyword.strip('\"'): [] for keyword in KEYWORDS
}
subreddit = reddit.subreddit(SUBREDDIT_NAME)


def fetch_posts(keyword, limit, rep):
    posts = list(subreddit.search(f'title:{keyword}', sort="new", limit=limit))
    if len(posts)<LIMIT and rep<10:
        return fetch_posts(keyword, limit+10, rep+1)
    
    return posts


for keyword in KEYWORDS:
    posts = fetch_posts(keyword, LIMIT, 1)
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
            "has_links": check_post_links(submission),
            "comments": []
        }

        for top_comment in submission.comments:
            body_text = top_comment.body
            post_data["comments"].append({
                'url': f"https://www.reddit.com{top_comment.permalink}",
                'date': dt.fromtimestamp(top_comment.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                'comment_id': top_comment.id,
                'votes': top_comment.score,
                "body": body_text,
                "has_multimedia": check_media_in_text(body_text),
                "has_links": check_links_in_text(body_text),
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
        total += 1
        total += count_all_replies(comment.get("replies", []))
    return total

def flatten_all_comments(comments):
    all_comments = []
    for comment in comments:
        all_comments.append(comment)
        all_comments.extend(flatten_all_comments(comment.get("replies", [])))
    return all_comments

# 9. Calculate Metrics
total_posts = 0
total_top_comments = 0
total_all_comments = 0
posts_with_media = 0
posts_with_links = 0
comments_with_media = 0
comments_with_links = 0

for keyword_posts in structured_data.values():
    for post in keyword_posts:
        total_posts += 1
        total_top_comments += len(post["comments"])
        all_comments = flatten_all_comments(post["comments"])
        total_all_comments += len(all_comments)

        if post.get("has_multimedia"):
            posts_with_media += 1
        if post.get("has_links"):
            posts_with_links += 1

        for comment in all_comments:
            if comment.get("has_multimedia"):
                comments_with_media += 1
            if comment.get("has_links"):
                comments_with_links += 1

avg_top_comments = total_top_comments / total_posts if total_posts else 0
avg_all_comments = total_all_comments / total_posts if total_posts else 0

# 11. Logging
timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
log_output = f"""
📊 Extraction Summary — {timestamp}
Subreddit Name   : {SUBREDDIT_NAME}
Keywords Used    : {', '.join(KEYWORDS)}
Limit per Keyword: {LIMIT}

Total posts collected          : {total_posts}
Total top-level comments       : {total_top_comments}
Total comments (with replies)  : {total_all_comments}

Posts with multimedia          : {posts_with_media}
Posts with links               : {posts_with_links}
Comments/replies with media    : {comments_with_media}
Comments/replies with links    : {comments_with_links}

Average top comments/post      : {avg_top_comments:.2f}
Average total comments/post    : {avg_all_comments:.2f}
"""

print(log_output)

os.makedirs("data", exist_ok=True)
with open("data/UKPolitics_extraction_log.txt", "a", encoding="utf-8") as log_file:
    log_file.write(log_output + "\n" + "-" * 60 + "\n")



