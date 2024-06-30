import gspread
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline


def get_nlp():
    # Load the tokenizer and model
    model_name = "HooshvareLab/bert-fa-base-uncased-sentiment-snappfood"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    # Create a pipeline for sentiment analysis
    return pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)


def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('dentist-scrapper-312bdd3b19c6.json', scope)
    gc = gspread.authorize(credentials)
    return gc.open('dentists').sheet1


def calculate_final_score(row):
    comments_column_num = 8
    star_column_num = 9
    comments = row[comments_column_num-1].split('_________________')
    result = nlp(comments)
    predicted_score = 5 * np.average([i['score'] for i in result])
    star = float(row[star_column_num-1])
    return (predicted_score + star) / 2


if __name__ == '__main__':
    nlp = get_nlp()
    sheet = get_sheet()
    source_data = sheet.get_all_values()
    final_score_column_num = 10
    sheet.update_cell(1, final_score_column_num, "final score")

    for index, row in enumerate(source_data):
        if index == 0 or len(row) < final_score_column_num or row[final_score_column_num-1]:
            continue
        score = calculate_final_score(row)

        sheet.update_cell(index + 1, final_score_column_num, score)
