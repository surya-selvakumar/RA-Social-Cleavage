import praw
import json
import time
from tqdm import tqdm
import datetime

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
KEYWORDS = "universal income OR minimum wage OR council tax OR income tax OR national insurance OR poverty"
LIMIT = 250  # Adjust or use None for unlimited

# 4. Recursive function to get nested replies
def get_replies(comment):
    if isinstance(comment, praw.models.MoreComments):
        return []
    replies = []
    for reply in comment.replies:
        replies.append({
            "body": reply.body,
            "replies": get_replies(reply)
        })
    return replies

# 5. Collect data with progress bar
structured_data = []
subreddit = reddit.subreddit(SUBREDDIT_NAME)
posts = list(subreddit.search(KEYWORDS, sort="new", limit=LIMIT))

print(f"🔍 Found {len(posts)} posts. Starting extraction...")

for submission in tqdm(posts, desc="Extracting posts", unit="post"):
    submission.comments.replace_more(limit=None)
    
    post_data = {
        "title": submission.title,
        "comments": []
    }

    for top_comment in submission.comments:
        post_data["comments"].append({
            "body": top_comment.body,
            "replies": get_replies(top_comment)
        })

    structured_data.append(post_data)
    time.sleep(1)  # To be nice to Reddit API

# 6. Save to JSON
file_name = f"data/{SUBREDDIT_NAME}_data_op.json"
with open(file_name, "w", encoding="utf-8") as f:
    json.dump(structured_data, f, ensure_ascii=False, indent=2)

print(f"Data saved to {file_name}")



# 7. Metrics Function
def count_all_replies(comments):
    total = 0
    for comment in comments:
        total += 1
        total += count_all_replies(comment.get("replies", []))
    return total

total_posts = len(structured_data)
total_top_comments = sum(len(post["comments"]) for post in structured_data)
total_all_comments = sum(count_all_replies(post["comments"]) for post in structured_data)
avg_top_comments = total_top_comments / total_posts if total_posts else 0
avg_all_comments = total_all_comments / total_posts if total_posts else 0


# 8. Logging
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_output = f"""
Extraction Summary — {timestamp}
Subreddit Name - {SUBREDDIT_NAME}
Keywords Used - {KEYWORDS}
Limit Set - {LIMIT}

Total posts collected: {total_posts}
Total top-level comments: {total_top_comments}
Total comments including replies: {total_all_comments}
Avg top-level comments per post: {avg_top_comments:.2f}
Avg total comments per post: {avg_all_comments:.2f}
"""

print(log_output)

with open("data/UKPolitics_extraction_log.txt", "a", encoding="utf-8") as log_file:
    log_file.write(log_output + "\n" + "-" * 60 + "\n")