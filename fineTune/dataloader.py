import numpy as np
import pandas as pd
import re
import json
import warnings

warnings.filterwarnings('ignore')


def clean_text(text):
    if isinstance(text, str):
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)  
        text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)  
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    return ''

def filter_bot(text):
    return isinstance(text, str) and 'i am a bot' in text.lower() #iamabot' in re.sub(r'\s+', '', text)


def clean_dataset(df):

    for idx, text in df['comment_body'].items():
        cleaned_text = clean_text(text)
        if filter_bot(cleaned_text):
            df.drop(idx, inplace=True)

    df = df[~df['comment_stance'].isna()]

    df['comment_stance'] = df['comment_stance'].replace({'neutral ': 'neutral', 'approve ': 'approve', 'disapprove ':'disapprove'})
    df['comment_body'] = df['comment_body'].apply(clean_text)

    return df


def convert_to_jsonl(df, output_path):
    instr = ("You are a social media stance classifier. "
             "Read the COMMENT and decide whether the author *approves*, "
             "*disapproves*, or is *neutral* towards the stated POST. "
             "Respond *only* with the label (approve, disapprove, or neutral).")
    with open(output_path, 'w', encoding='utf‑8') as f:
        for _, row in df.iterrows():
            rec = {"instruction": instr, 
                    "input": f"POST: '{row['post_title']}'\COMMENT: '{row['comment_body']}'", 
                    "output": row['comment_stance']}
            f.write(json.dumps(rec) + "\n")


def main():
    data_path = '../data/tenpct_comments_manual_labelled.csv'
    output_path = '../data/tenpct_jsn.jsonl'
    df = pd.read_csv(data_path)
    cleaned_df = clean_dataset(df)
    convert_to_jsonl(cleaned_df, output_path)


if __name__=='__main__':
    main()
