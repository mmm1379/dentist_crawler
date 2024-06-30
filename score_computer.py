import gspread
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline


def initialize_nlp():
    global nlp
    # Load the tokenizer and model
    model_name = "HooshvareLab/bert-fa-base-uncased-sentiment-snappfood"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    # Create a pipeline for sentiment analysis
    nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)


def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('dentist-scrapper-312bdd3b19c6.json', scope)
    gc = gspread.authorize(credentials)
    return gc.open('dentists').sheet1


def calculate_final_score():
    comments = row[7].split('_________________')
    result = nlp(comments)
    return np.average([i['score'] for i in result])


if __name__ == '__main__':

    initialize_nlp()
    sheet = get_sheet()
    source_data = sheet.get_all_values()

    for index, row in enumerate(source_data):
        if index == 1:
            continue
        score = calculate_final_score()
        sheet.update_cell(index + 1, 8, score)
