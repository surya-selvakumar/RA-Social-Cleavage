import json
import pandas as pd

file_path = "./data/ukpolitics_180425.json"
with open(file_path, "r") as f:
    data = json.load(f)

categories = ["universal income", "minimum wage", "council tax", "income tax", "national insurance", "poverty"]

all_posts, all_comments, all_replies = [], [], []

def extract_replies(replies, post_info, comment_info):
    extracted = []
    for reply in replies:
        reply_row = {
            **post_info,
            **comment_info,
            "reply_id": reply.get("reply_id"),
            "reply_url": reply.get("url"),
            "reply_date": reply.get("date"),
            "reply_votes": reply.get("votes"),
            "reply_body": reply.get("body"),
            "reply_has_multimedia": reply.get("has_multimedia"),
            "reply_has_links": reply.get("has_links")
        }
        extracted.append(reply_row)
        if reply.get("replies"):
            extracted.extend(extract_replies(reply["replies"], post_info, {
                "comment_id": reply.get("reply_id"),
                "comment_url": reply.get("url"),
                "comment_date": reply.get("date"),
                "comment_votes": reply.get("votes"),
                "comment_body": reply.get("body"),
            }))
    return extracted

for category in categories:
    posts = data.get(category, [])
    for post in posts:
        post_info = {
            "category": category,
            "post_id": post.get("id"),
            "post_url": post.get("url"),
            "post_date": post.get("date"),
            "post_votes": post.get("votes"),
            "post_title": post.get("title"),
            "post_has_multimedia": post.get("has_multimedia"),
            "post_has_links": post.get("has_links"),
        }
        all_posts.append(post_info)
        comments = post.get("comments", [])
        for comment in comments:
            # print(post.get('url'))
            comment_info = {
                "category": category,
                "post_id": post.get("id"),
                "post_url": post.get('url'),
                "comment_id": comment.get("comment_id"),
                "comment_url": comment.get("url"),
                "comment_date": comment.get("date"),
                "comment_votes": comment.get("votes"),
                "comment_body": comment.get("body"),
                "comment_has_multimedia": comment.get("has_multimedia"),
                "comment_has_links": comment.get("has_links"),
            }
            all_comments.append(comment_info)
            replies = comment.get("replies", [])
            all_replies.extend(extract_replies(replies, post_info, comment_info))

# Save to CSV
pd.DataFrame(all_posts).to_csv("./data/posts.csv", index=False)
pd.DataFrame(all_comments).to_csv("./data/comments.csv", index=False)
pd.DataFrame(all_replies).to_csv("./data/replies.csv", index=False)

print("✅ posts.csv, comments.csv, and replies.csv saved successfully.")
