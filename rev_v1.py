import praw
import json
import time
from tqdm import tqdm
import datetime
import os

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
LIMIT = 10  # Adjust or use None for unlimited

# 4. Recursive function to get nested replies
def get_replies(comment):
    if isinstance(comment, praw.models.MoreComments):
        return []  # Avoid getting a 'MoreComments' object, which is not a real comment
    replies = []
    for reply in comment.replies:
        replies.append({
            'url': f"https://www.reddit.com{reply.permalink}",  # Fix: Use permalink to get the comment URL
            'date': reply.created_utc,
            'reply_id': reply.id,
            'votes': reply.score,
            "body": reply.body,
            "replies": get_replies(reply)  # Recursively fetch nested replies
        })
    return replies

# 5. Collect data with progress bar
structured_data = {
    keyword.strip('\"'): [] for keyword in KEYWORDS
}
subreddit = reddit.subreddit(SUBREDDIT_NAME)

for keyword in KEYWORDS:
    # Use `title:` prefix to search only in post titles, ensuring exact match
    posts = list(subreddit.search(f'title:{keyword}', sort="new", limit=LIMIT))

    print(f"🔍 Found {len(posts)} posts for the keyword: {keyword}. Starting extraction...")

    for submission in tqdm(posts, desc="Extracting posts", unit="post"):
        submission.comments.replace_more(limit=None)  # This makes sure we load all comments
        
        post_data = {
            'url': f"https://www.reddit.com{submission.permalink}",  # Use permalink for post URL
            'date': submission.created_utc,
            'id': submission.id,
            'votes': submission.score,
            "title": submission.title,
            "comments": []
        }

        # Collect data for top comments and replies, but not used in the search query
        for top_comment in submission.comments:
            post_data["comments"].append({
                'url': f"https://www.reddit.com{top_comment.permalink}",  # Use permalink for top-level comment URL
                'date': top_comment.created_utc,
                'comment_id': top_comment.id,
                'votes': top_comment.score,
                "body": top_comment.body,
                "replies": get_replies(top_comment)  # Get all replies recursively
            })

        structured_data[keyword.strip('\"')].append(post_data)
        time.sleep(1)  # To be nice to Reddit API

# 6. Save to JSON
file_path = os.path.join(f"data/{SUBREDDIT_NAME}_data.json")
if os.path.exists(file_path):
        i = 1
        while os.path.exists(os.path.join('data', f"{SUBREDDIT_NAME}_{i}.json")):
            i += 1
        file_path = os.path.join('data', f"{SUBREDDIT_NAME}_{i}.json")

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(structured_data, f, ensure_ascii=False, indent=2)

print(f"Data saved to {file_path}")

# 7. Metrics Function
def count_all_replies(comments):
    total = 0
    for comment in comments:
        total += 1  # Count the comment itself
        total += count_all_replies(comment.get("replies", []))  # Recursively count replies
    return total

# total_posts = len(structured_data)
# total_top_comments = sum(len(post["comments"]) for post in structured_data)
# total_all_comments = sum(count_all_replies(post["comments"]) for post in structured_data)
# avg_top_comments = total_top_comments / total_posts if total_posts else 0
# avg_all_comments = total_all_comments / total_posts if total_posts else 0

# # 8. Logging
# timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# log_output = f"""
# Extraction Summary — {timestamp}
# Subreddit Name - {SUBREDDIT_NAME}
# Keywords Used - {KEYWORDS}
# Limit Set - {LIMIT}

# Total posts collected: {total_posts}
# Total top-level comments: {total_top_comments}
# Total comments including replies: {total_all_comments}
# Avg top-level comments per post: {avg_top_comments:.2f}
# Avg total comments per post: {avg_all_comments:.2f}
# """

# print(log_output)

# with open("data/UKPolitics_extraction_log.txt", "a", encoding="utf-8") as log_file:
#     log_file.write(log_output + "\n" + "-" * 60 + "\n")
