import re
import requests
import time
from tqdm import tqdm
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score


def clean_text(text):
    if isinstance(text, str):
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)  
        text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)  
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    return ''

def filter_bot(text):
    return isinstance(text, str) and 'i am a bot' in text.lower() #iamabot' in re.sub(r'\s+', '', text)

def strip_content(text):
    text = re.sub(r'[^A-Za-z0-9\s]', '', text.lower())

    try:
        stance_index = text.index('stance')
    except ValueError:
        stance_index = 0

    try:
        arg_index = text.index('rationale')
    except ValueError:
        arg_index = len(text)

    if arg_index > stance_index:
        stance_text = text[stance_index:arg_index]
    else:
        stance_text = text[stance_index:]

    stance = 'disapprove' if 'disagree' in stance_text else 'approve'

    argument = text[arg_index:].split(' ')
    try:
        argument.remove('rationale')
    except:
        pass
    argument = ' '.join(argument)

    return stance, argument

# Prompt templates
def response_prompt(title, comment):
    return f"""You are an expert in political discourse analysis.

    Post Title: "{title}"
    Comment: "{comment}"

    Task 1: Does the comment AGREE or DISAGREE with the opinion expressed in the title? Reply only with 'agree', 'disagree'.

    Task 2: Briefly explain the rationale behind the comment in 1-2 sentences.

    Respond in the following format:
    Stance: <stance>
    Rationale: <explanation>
    """

def query_ollama(prompt, mdl_idx):
    models_dict = {0: 'gemma3:12b', 1: 'gemma3:4b', 2: 'deepseek-r1:8b'}
    url = "http://localhost:11434/api/generate"
    data = {
        "model": models_dict[mdl_idx],
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print("Error:", e)
        return ""

def apply_on_df(df):
    selected_mdl_idx = 0
    for idx, row in tqdm(df.iterrows(), desc='Processing', total=len(df), dynamic_ncols=True):
        # First pass
        prompt1 = response_prompt(row['post_title'], row['comment_body'])
        response1 = query_ollama(prompt1, selected_mdl_idx)
        stance1, arg1 = strip_content(response1)

        # Second independent recheck (no yes/no)
        prompt2 = response_prompt(row['post_title'], row['comment_body'])
        response2 = query_ollama(prompt2, selected_mdl_idx)
        stance2, arg2 = strip_content(response2)

        df.at[idx, 'llm_stance'] = stance1
        df.at[idx, 'llm_argument'] = arg1
        df.at[idx, 'llm_stance2'] = stance2
        df.at[idx, 'llm_argument2'] = arg2

        df.at[idx, 'llm_stance3'] = stance1 if stance1==stance2 else stance2

        time.sleep(1)

    return df


def load_process_df():
    df = pd.read_csv('./data/manually_labelled.csv')

    for idx, text in df['comment_body'].items():
        cleaned_text = clean_text(text)
        if filter_bot(cleaned_text):
            df.drop(idx, inplace=True)

    df = df[~df['comment_stance'].isna()]
    df['comment_body'] = df['comment_body'].apply(clean_text)

    return df 

def save_log(acc_scores):
    file_path = '/data/log.txt'
    with open(file_path, 'w') as f:
        f.write(
            f"\nAccuracy : {":.2f".format(acc_scores[0])}\nAccuracy : {":.2f".format(acc_scores[1])}\nAccuracy : {":.2f".format(acc_scores[2])}"
        )

    

def main():
    df = load_process_df()
    result_df = apply_on_df(df)
    result_df.to_csv('/data/llm_labelled_2405.csv')
    y_true, ypred1, ypred2, ypred3 = result_df['comment_stance'], result_df['llm_stance'], result_df['llm_stance2'], result_df['llm_stance3']
    acc_score1 = accuracy_score(y_true, ypred1)
    acc_score2 = accuracy_score(y_true, ypred2)
    acc_score3 = accuracy_score(y_true, ypred3)
    save_log([acc_score1, acc_score2, acc_score3])

    print([acc_score1, acc_score2, acc_score3])


if __name__=='__main__':
    main()




