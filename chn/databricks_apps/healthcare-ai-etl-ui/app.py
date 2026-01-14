"""
Healthcare AI ETL Platform - Databricks App
A demonstration UI for an AI-driven ETL platform on Databricks
"""
from flask import Flask, render_template_string

app = Flask(__name__)

# Read the HTML content
with open('index.html', 'r') as f:
    html_content = f.read()

@app.route('/')
def index():
    """Serve the main application"""
    return render_template_string(html_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
