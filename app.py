from flask import Flask, render_template, url_for
from bot import app, Post, db
from datetime import datetime

@app.route('/')
def index():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15000)
