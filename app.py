from flask import Flask, redirect, render_template, request
import os
import requests

app = Flask(__name__)
app.config['FLASK_DEBUG'] = True
app.config['STATIC_FOLDER'] = '/static'
app.config['TEMPLATES_FOLDER'] = '/templates'

gh_token = os.getenv('GITHUB_TOKEN')

def gh_contents(owner, repo, path):
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        {'Authorization': f'token {gh_token}'}
    )
    return r.json()

@app.route("/")
def home():
    contents = gh_contents('massive-wiki', 'massive-wiki', '')

    return render_template(
        'home.html',
        contents = contents
    )
