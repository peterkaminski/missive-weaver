from flask import Flask, redirect, render_template, request
import json

app = Flask(__name__)
app.config['FLASK_DEBUG'] = True
app.config['STATIC_FOLDER'] = '/static'
app.config['TEMPLATES_FOLDER'] = '/templates'

@app.route("/")
def home():
    return render_template(
        'home.html'
    )
