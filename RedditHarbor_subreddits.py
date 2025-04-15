# Data collection via subreddits
### see https://github.com/socius-org/RedditHarbor/

# 1. set up authentication
SUPABASE_URL = "https://llcmbxgkaifznmtwesud.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsY21ieGdrYWlmem5tdHdlc3VkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNDAwNTExNCwiZXhwIjoyMDQ5NTgxMTE0fQ.tR3OTNuFPH951TQSArWtmPizm5D1fzPE6stzwDp0DRE" #Remember to use "service_role/secret" key, not "anon/public" key 

REDDIT_PUBLIC = "cSGrCpPxEQBLv42bvRsdrg"
REDDIT_SECRET = "v7ihmm1jvIL3YnVA7WmGBabnvehZAg"
REDDIT_USER_AGENT = "Brave-Equivalent-957" #format - <institution:project-name (u/reddit-username)>

DB_CONFIG = {
  "user": "test_redditor",
  "submission": "test_submission", 
  "comment": "test_comment"
} #define the database table names to store the data

# 2. set up redditharbor configuration
import redditharbor.login as login 

reddit_client = login.reddit(public_key=REDDIT_PUBLIC, secret_key=REDDIT_SECRET, user_agent=REDDIT_USER_AGENT)
supabase_client = login.supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

from redditharbor.dock.pipeline import collect

collect = collect(reddit_client=reddit_client, supabase_client=supabase_client, db_config=DB_CONFIG)

# 3. define key collection elements and collect data
# subreddits = ["ukpolitics"]
# sort_types = ["new"] 

## 3.1 collect subreddits
# collect.subreddit_submission(subreddits, sort_types, limit=5) # only submissions, collect the 5 hottest and 5 top submissions from selected subreddits, along with the associated user data, and store them in the configured database tables
# collect.subreddit_comment(subreddits, sort_types, limit=5, level=2) # comments + users, comments from the 5 hottest and 5 top submissions from the specified subreddits, up to a depth of 2 reply levels
# collect.subreddit_submission_and_comment(subreddits, sort_types, limit=100000000, level=None) # collect submissions, associated comments and users in one go

## 3.2 collect keywords under subreddits
subreddits = ["ukpolitics"]
query = "universal income OR minimum wage OR council tax OR income tax OR national insurance OR poverty"
collect.submission_by_keyword(subreddits, query, limit=100000000)

## 3.3 fetch comments and users from specified submissions

### fetch comments
from redditharbor.utils import fetch 
fetch_submission = fetch.submission(supabase_client=supabase_client, db_name=DB_CONFIG["submission"])
submission_ids = fetch_submission.id(limit=None) # Limiting to 100 submission IDs for demonstration. Set limit=None to fetch all submission IDs
collect.comment_from_submission(submission_ids=submission_ids, level=None) #Set level=None to collect entire comments

### fetch users
# from redditharbor.utils import fetch
# fetch_user = fetch.user(supabase_client=supabase_client, db_name=DB_CONFIG["user"])
# users = fetch_user.name(limit=100) #This will fetch the first 100 user names from the user database. Set limit=None to fetch entire user names.  
# collect.submission_from_user(users=users, sort_types=["controversial"], limit=10)


# 4. downloading data
from redditharbor.utils import download

### save all columns from the “submissions” table to a submission.csv file in the specified folder directory
download = download.submission(supabase_client, DB_CONFIG["submission"])
download.to_csv(columns="all", file_name="submission", file_path="Downloads")

## customize the output by specifying columns and file formats:
# cols = ["submission_id", "title", "score"]
# download.to_json(columns=cols, file_name="submission", file_path="<D:\Work\Dropbox\Digital social cleavage\datasets\digital data\reddit\sample data analysis\subreddit data>")

## download image files from the submission data
# download = download.submission(supabase_client, DB_CONFIG["submission"])
# download.to_img(file_path="<D:\Work\Dropbox\Digital social cleavage\datasets\digital data\reddit\sample data>")

## download comment data:
download = download.comment(supabase_client, DB_CONFIG["comment"])
download.to_csv(columns="all", file_name="comment", file_path="Downloads")

## download user data:
#download = download.user(supabase_client, DB_CONFIG["user"])
#download.to_csv(columns="all", file_name="user", file_path="<D:\Work\Dropbox\Digital social cleavage\datasets\digital data\reddit\sample data analysis\subreddit data>")