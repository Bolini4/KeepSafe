from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/passwordGen")
def passwordGen():
    return render_template("passge.html")