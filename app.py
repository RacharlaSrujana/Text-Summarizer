from flask import Flask, render_template, request, jsonify
from newspaper import Article
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from gtts import gTTS
from deep_translator import GoogleTranslator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import os
from time import time
from bs4 import BeautifulSoup
import requests
# from rouge_score import rouge_scorer  # Importing ROUGE scorer

app = Flask(__name__)

def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)['compound']
    return "Happy 😊" if score > 0.05 else "Sad 😞" if score < -0.05 else "Neutral 😐"

def generate_summary(text, length):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    num_sentences = 2 if length == "short" else 5 if length == "medium" else 8
    return " ".join(str(sentence) for sentence in summarizer(parser.document, num_sentences))

"""
def calculate_rouge(reference, generated_summary):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, generated_summary)
    return {
        "ROUGE-1": scores["rouge1"].fmeasure,
        "ROUGE-2": scores["rouge2"].fmeasure,
        "ROUGE-L": scores["rougeL"].fmeasure
    }
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        url = request.form.get("url")
        summary_length = request.form.get("summary_length", "medium")
        language = request.form.get("language", "en")

        if not url:
            return jsonify({"error": "No URL provided"}), 400

        # Extract article details
        article = Article(url)
        article.download()
        article.parse()

        details=scrape_news(url)
        # authors = ", ".join(article.authors) if article.authors else "Unknown"
        # publish_date = article.publish_date.strftime("%Y-%m-%d") if article.publish_date else "Not Available"
        authors=details[0]
        publish_date=details[1]

        summary = generate_summary(article.text, summary_length)
        sentiment = analyze_sentiment(summary)

        # Calculate ROUGE score
        # rouge_scores = calculate_rouge(article.text, summary)

        # Translate summary if needed
        translated_summary = GoogleTranslator(source="auto", target=language).translate(summary)

        # Convert text to speech
        tts = gTTS(text=translated_summary, lang=language)
        tts.save("static/summary_audio.mp3")

        return render_template("index.html", summary=translated_summary, authors=authors, publish_date=publish_date, sentiment=sentiment, time=int(time()))
    # rouge_scores=rouge_scores
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def scrape_news(url):
    headers = {"User-Agent": "Mozilla/5.0"}  # Prevents blocking
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {"error": "Failed to retrieve the article"}

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract headline
    headline = soup.find("h1").text.strip() if soup.find("h1") else "No headline found"
    
    # Extract author and date
    byline = soup.find("div", class_="xf8Pm byline")
    if byline:
        byline_text = byline.text.strip().split("/")  # Split based on slashes

        # Extract author
        author = byline_text[0].strip() if len(byline_text) > 0 else "Unknown Author"
        
        # Extract date and clean it
        date = byline_text[-1].strip().replace("Updated:", "").strip()
        date = date.split(",")[0] + "," + date.split(",")[1]  # Keep only 'Month Day, Year'
    else:
        author = "Unknown Author"
        date = "Unknown Date"
    return (author,date)


if __name__ == '__main__':
    app.run(debug=True)


