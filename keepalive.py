from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running", 200

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
