import os
from flask import Flask, render_template, request
import google.generativeai as genai
import PyPDF2
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

app = Flask(__name__)

#Use Google AI Studio to generate API Key.
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("No GOOGLE_API_KEY found. Please set the environment variable.")

genai.configure(api_key=API_KEY)

# Initialize the Gemini 2.5 Model or your Choice Model 
model = genai.GenerativeModel("gemini-2.5-flash")

def predict_fake_or_real_email_content(text):
    prompt = f"""
    Analyze the following text for scam/phishing indicators. 
    Classify as: **Real/Legitimate** or **Scam/Fake**.
    If it's a scam, explain why in simple paragraph dont write in bold text. First line should be Real/Legitimate or Scam/Fake then reasons below it. 
    
    Text: {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error during analysis: {str(e)}"

def url_detection(url):
    prompt = f"""
    Classify this URL into one of these categories: True Website URL, phishing Website URL, malware, defacement.
    Return ONLY the category name in lowercase.
    
    URL: {url}
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower()
    except Exception as e:
        return "error"

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/scam/', methods=['POST'])
def detect_scam():
    if 'file' not in request.files:
        return render_template("index.html", message="No file selected.")

    file = request.files['file']
    if file.filename == '':
        return render_template("index.html", message="No file selected.")

    extracted_text = ""
    try:
        if file.filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            extracted_text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif file.filename.endswith('.txt'):
            extracted_text = file.read().decode("utf-8")
        else:
            return render_template("index.html", message="Unsupported file type.")

        if not extracted_text.strip():
            return render_template("index.html", message="Could not extract text from file.")

        result = predict_fake_or_real_email_content(extracted_text)
        return render_template("index.html", message=result)
    except Exception as e:
        return render_template("index.html", message=f"Processing error: {str(e)}")

@app.route('/predict', methods=['POST'])
def predict_url():
    url = request.form.get('url', '').strip()
    if not url:
        return render_template("index.html", message="Please enter a URL.")
    
    classification = url_detection(url)
    return render_template("index.html", input_url=url, predicted_class=classification)

if __name__ == '__main__':
    app.run(debug=True, port=6005)
