import gspread
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

# Load the tokenizer and model
model_name = "HooshvareLab/bert-fa-base-uncased-sentiment-snappfood"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Create a pipeline for sentiment analysis
nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Path to the downloaded JSON key file from the Google Cloud Console
credentials = ServiceAccountCredentials.from_json_keyfile_name('dentist-scrapper-312bdd3b19c6.json', scope)

# Authenticate with Google Sheets
gc = gspread.authorize(credentials)
sheet = gc.open('dentists').sheet1

# Get all values from the source sheet
source_data = sheet.get_all_values()


for index, row in enumerate(source_data):
    if index == 1:
      continue
    # Convert row to a list of floats (assuming the data is numerical)
    comments = row[7].split('_________________')
    result = nlp(comments)
    score = np.average([i['score'] for i in result])
    sheet.update_cell(index+1, 8, score)
