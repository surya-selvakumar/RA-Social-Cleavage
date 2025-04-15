import json 
import os

def string_match(keyword, statement):
    return keyword.lower() in statement.lower()

def verify_keyword_occurence(data):

    unrelated = {}
    
    for keyword, posts in data.items():
        unrelated[keyword] = []
        for post in posts:
            if keyword.lower() not in post['title'].lower():
                unrelated[keyword].append(post['title'])

    print(unrelated)


if __name__=='__main__':
    filename = os.path.join('data', 'ukpolitics_2.json')
    with open(filename, 'r') as json_file:
        data = json.load(json_file)

    verify_keyword_occurence(data)