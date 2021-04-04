import base64
from flask import Flask, make_response, redirect, render_template, request
from hashlib import sha256
import json
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
        headers={'Authorization': f'token {gh_token}'}
    )
    return r.json()

def gh_rate_limit():
    r = requests.get(
        f"https://api.github.com/rate_limit",
        headers={'Authorization': f'token {gh_token}'}
    )
    return r.json()

@app.route("/admin")
def admin():
    return render_template(
        'admin-index.html'
    )

@app.route("/admin/token")
def admin_token():
    response = make_response(
        sha256(gh_token.encode('utf-8')).hexdigest(),
        200
    )
    response.mimetype = "text/plain"
    return response

@app.route("/admin/rate_limit")
def admin_rate_limit():
    response = make_response(
        json.dumps(gh_rate_limit(), indent=2),
        200
    )
    response.mimetype = "text/plain"
    return response

@app.route("/wiki/<user>/<repo>/")
@app.route("/wiki/<user>/<repo>/<path>")
def wiki(user, repo, path=''):
    contents = gh_contents(user, repo, path)

    if 'message' in contents:
        response = make_response(
            f'Error: {contents["message"]}',
            502
        )
        response.mimetype = "text/plain"
        return response

    if isinstance(contents, list):
        # we're looking at a directory
        items = []
        files = []
        dirs = []
        for item in contents:
            if item['type']=='file' and item['name'].endswith('.md'):
                file = {}
                file['name'] = item['name'][:-3] # remove '.md'
                if item['download_url'].startswith('https://raw.githubusercontent.com/'):
                    file['download_url'] = f'/wiki/{user}/{repo}/{item["download_url"].split("/", 6)[6]}'
                else:
                    file['download_url'] = item['download_url']
                files.append(file)
        return render_template(
            'wiki.html',
            items = files
        )
    elif isinstance(contents, dict):
        # we're looking at a file
        if contents['encoding'] != 'base64':
            response = make_response(
                f'Unknown encoding {contents["encoding"]}',
                502
            )
            response.mimetype = "text/plain"
            return response
        else:
            response = make_response(
#                f'<a href="{contents["html_url"]}">edit on GitHub</a>\n'+
                    base64.b64decode(contents["content"]),
                200
            )
            response.mimetype = "text/plain"
            return response
    else:
        # shouldn't get here
        exit(1)

