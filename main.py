from serpapi import GoogleSearch
import requests
import openai
import sys
from tqdm import tqdm
import time
from dotenv import load_dotenv
import os
import colorama
from termcolor import colored

# Load the .env file
load_dotenv()

colorama.init(autoreset=True)

open_ai_api_key = os.getenv("OPENAI_API_KEY")
browserless_api_key = os.getenv("BROWSERLESS_API_KEY")
serpapi_api_key = os.getenv("SERPAPI_API_KEY")
openai_model = "gpt-3.5-turbo-16k-0613"

openai.api_key = open_ai_api_key
headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
params = {'token': browserless_api_key}


def scrape(link):
    json_data = {
        'url': link,
        'elements': [{'selector': 'body'}],
    }
    response = requests.post('https://chrome.browserless.io/scrape', params=params, headers=headers, json=json_data)

    if response.status_code == 200:
        webpage_text = response.json()['data'][0]['results'][0]['text']
        return webpage_text
    else:
        print(f"Error: Unable to fetch content from {link}. Status code: {response.status_code}")
        return ""


def summarize(question, webpage_text):
    prompt = """You are an intelligent summarization engine. Extract and summarize the
  most relevant information from a body of text related to a question.

  Question: {}

  Body of text to extract and summarize information from:
  {}

  Relevant information:""".format(question, webpage_text[0:2500])

    response = openai.ChatCompletion.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    return response.choices[0].message.content


def final_summary(question, summaries):
    num_summaries = len(summaries)
    prompt = "You are an intelligent summarization engine. Extract and summarize relevant information from the {} points below to construct an answer to a question.\n\nQuestion: {}\n\nRelevant Information:".format(
        num_summaries, question)

    for i, summary in enumerate(summaries):
        prompt += "\n{}. {}".format(i + 1, summary)

    response = openai.ChatCompletion.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    return response.choices[0].message.content


def link(r):
    return r['link']


def search_results(question):
    search = GoogleSearch({
        "q": question,
        "api_key": serpapi_api_key,
        "logging": False
    })

    result = search.get_dict()
    return list(map(link, result['organic_results']))


def print_citations(links, summaries):
    print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + "CITATIONS" + colorama.Style.RESET_ALL)
    num_citations = min(len(links), len(summaries))
    for i in range(num_citations):
        print("\n", "[{}]".format(i + 1), links[i], "\n", summaries[i], "\n")


def main():
    print(colored("\nWHAT WOULD YOU LIKE ME TO SEARCH?\n", "cyan", attrs=["bold"]))
    question = input()
    print("\n")
    sys.stdout = open(os.devnull, 'w')  # disable print
    links = search_results(question)
    sys.stdout = sys.__stdout__  # enable print
    webpages = []
    summaries = []

    # Display progress bar
    with tqdm(total=100, desc="Loading", ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} ", unit=" percent") as pbar:
        for i in range(4):
            pbar.update(12.5)
            time.sleep(0.1)
            if i < len(links):
                webpages.append(scrape(links[i]))
            pbar.update(12.5)
            time.sleep(0.1)
            if i < len(webpages):
                summaries.append(summarize(question, webpages[i]))

    answer = final_summary(question, summaries)
    print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + "\n\nHERE IS THE ANSWER\n" + colorama.Style.RESET_ALL)
    print(answer, "\n")
    print_citations(links, summaries)


if __name__ == "__main__":
    main()