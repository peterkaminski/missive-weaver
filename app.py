from flask import Flask, redirect, render_template, request
import json

# GitHub interface
from github import Github # pip install PyGithub

app = Flask(__name__)
app.config['FLASK_DEBUG'] = True
app.config['STATIC_FOLDER'] = '/static'
app.config['TEMPLATES_FOLDER'] = '/templates'

g = Github()

@app.route("/")
def home():

    repo_files = []
    repo = g.get_repo("PyGithub/PyGithub")
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            repo_files.append(file_content)

    return render_template(
        'home.html',
        repo_files = repo_files
    )
