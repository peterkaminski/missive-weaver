import base64
from flask import Flask, make_response, redirect, render_template, request, send_from_directory
from hashlib import sha256
import json
import os
import requests

from datetime import timezone, datetime

from markdown import Markdown
from mdx_wikilink_plus.mdx_wikilink_plus import WikiLinkPlusExtension
md_configs = {
    'mdx_wikilink_plus': {
#        'base_url': '/static',
        'end_url': '.md',
        'url_whitespace': '%20',
        'url_case': 'none',
        'label_case': 'none',
    },
}
md = Markdown(extensions=['mdx_wikilink_plus'], extension_configs=md_configs)

app = Flask(__name__)
app.config.from_object('config')

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

@app.route("/mwb-static/<path:path>")
def mwb_static(path):
    print(path)
    return send_from_directory('templates/mwb-static', path)

@app.route("/wiki/<user>/<repo>/")
@app.route("/wiki/<user>/<repo>/<path:path>")
def wiki(user, repo, path=''):
    contents = gh_contents(user, repo, path)

    print(f'user: {user}')
    print(f'repo: {repo}')
    print(f'path: {path}')

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
            if item['type']=='dir' and not item['name'].startswith('.'):
                dir = {}
                dir['name'] = item['name'] + '/'
                dir['download_url'] = item['url']
                if item['url'].startswith('https://api.github.com/repos/'):
                    dir['download_url'] = f'/wiki/{user}/{repo}/{item["url"].split("/", 7)[7]}'
                dirs.append(dir)
            if item['type']=='file' and item['name'].endswith('.md'):
                file = {}
                file['name'] = item['name'][:-3] # remove '.md'
                if item['download_url'].startswith('https://raw.githubusercontent.com/'):
                    file['download_url'] = f'/wiki/{user}/{repo}/{item["download_url"].split("/", 6)[6]}'
                else:
                    file['download_url'] = item['download_url']
                files.append(file)
            else:
                # ignored files and dot-dirs
                pass
        return render_template(
            'wiki.html',
            items = dirs+files
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
            build_time = datetime.now(timezone.utc).strftime("%A, %B %d, %Y at %H:%M UTC")
            markdown_body = md.convert(base64.b64decode(contents["content"]).decode('utf-8'))
            html = render_template('page.html', build_time=build_time, wiki_title=app.config['WIKI_TITLE'], author=app.config['WIKI_AUTHOR'], repo=app.config['WIKI_REPO'], license=app.config['WIKI_LICENSE'], title="Missive Weaver", markdown_body=markdown_body)
            response = make_response(html, 200)
            response.mimetype = "text/html"
            return response
    else:
        # shouldn't get here
        exit(1)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template(
        'index.html'
    )

