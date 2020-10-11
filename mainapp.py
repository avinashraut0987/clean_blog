from flask import Flask, render_template, redirect, request, url_for, session, abort, jsonify, send_from_directory
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from werkzeug.utils import secure_filename
import datetime
import json
import smtplib
import os
import math

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

username = params['email']
password = params['password']

app = Flask(__name__)
app.secret_key = "clean_blog_123"

if (params['localhost']):
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{params['MYSQL_USER']}:{params['MYSQL_PASSWORD']}@{params['MYSQL_HOST']}/{params['MYSQL_DB']}"
else:
    print('error in config file')
mysql = MySQL(app)
db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12))
    email = db.Column(db.String(20), nullable=False)


class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img = db.Column(db.String(25), nullable=True)


@app.route('/')
def home():
    page = request.args.get('page')
    post = Post.query.filter_by().all()
    last = math.ceil(len(post)/int(params['nu_of_posts']))

    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    lenofpost = params['nu_of_posts']
    postlen = int(lenofpost)
    post = post[(page-1)*postlen:(page-1)*postlen+postlen]

    if (page == 1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page == last):
        prev = "/?page="+str(page-1)
        next = "#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)

    return render_template('index.html', params=params, post=post, prev=prev, next=next)


@app.route('/uploader', methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == 'POST':
            file = request.files['file']
            file.save(os.path.join(os.curdir + "/static/img", secure_filename(file.filename)))
            return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>')
def delete(sno):
    if ('user' in session and session['user'] == params['admin_username']):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', post=post, params=params)


@app.route('/addcontact', methods=['POST', 'GET'])
def add_contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        todateis = date.today()
        msg = request.form['msg']
        try:
            entry = Contact(name=name, phone_num=phone, msg=msg, date=todateis, email=email)
            db.session.add(entry)

            db.session.commit()

            # massag = "\r\n".join([
            #     f"From: {username}",
            #     f"To: {username}",
            #     "Subject: Just a message",
            #     "",
            #     f"{msg}"
            # ])
            # server = smtplib.SMTP('smtp.gmail.com:587')
            # server.ehlo()
            # server.starttls()
            # server.login(username, password)
            # server.sendmail(username, username, massag)
            # server.quit()
            return redirect(url_for('contact'))

        except Exception as e:
            print(e)
            return 'email not sent', e
    else:
        redirect(url_for('contact'))


@app.route('/contact')
def contact():
    return render_template('contact.html', params=params)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_username']):
        post = Post.query.all()
        return render_template('dashboard.html', params=params, post=post)

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        if password == params['admin_password'] and email == params['admin_username']:
            session['user'] = email
            post = Post.query.all()
            return render_template('dashboard.html', params=params, post=post)

    post = Post.query.all()
    return render_template('loginpage.html', params=params, post=post)


@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == 'POST':
            title = request.form['title']
            tagline = request.form['tagline']
            slug = request.form['slug']
            content = request.form['content']
            imgfile = request.form['imgfile']
            todaydateis = date.today()
            if sno=='0':
                post = Post(title=title, tagline=tagline, slug=slug, content=content, img=imgfile, date=todaydateis)
                db.session.add(post)
                db.session.commit()
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img = imgfile
                post.date = todaydateis
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Post.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post)


app.debug = True
app.run()
