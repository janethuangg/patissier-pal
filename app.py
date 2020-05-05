from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
# from data import Articles
#https://stackoverflow.com/questions/52261686/issues-with-flask-mysqldb-using-python3-7?rq=1
#export DYLD_LIBRARY_PATH=/usr/local/mysql/lib/:$DYLD_LIBRARY_PATH
# from flask_ngrok import run_with_ngrok
from pymongo import MongoClient
from wtforms import Form, StringField, TextAreaField, PasswordField, validators

import json
import os
import copy
from passlib.hash import sha256_crypt

# from flask_login import (
#     LoginManager,
#     current_user,
#     login_required,
#     login_user,
#     logout_user,
# )
# from oauthlib.oauth2 import WebApplicationClient
# import requests

# MongoDB Config
client = MongoClient(os.environ.get('MONGO_URI'))
db = client.desserts

# # Google OAuth Config
# os.getenv("MYSQL_PASS")
# GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
# GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# GOOGLE_DISCOVERY_URL = (
#     "https://accounts.google.com/.well-known/openid-configuration"
# )
 
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
# run_with_ngrok(app)  # Start ngrok when app is run

#decorator function that restricts access to certain pages
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized - Please log in', 'danger')
            return redirect(url_for('login'))
    return wrap
    
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        
        user = {'name':name,'email':email,'username':username,'password':password,'pantry':[]}
        db.users.insert(user)
        flash("You are now registered and can log in", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form) 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        data = list(db.users.find({"username":username}))
        print(data)
        if data:
            data = data[0]
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                session['name'] = data['name']
                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = "Invalid login"
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = "Username not found"
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out", 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/enter_recipe', methods=['GET','POST'])
def enter_recipe():
    if request.method == 'POST':
        selected_video = request.form.get('video')
        
        mongo_response1 = db.videos.find({"title":selected_video})
        selected_ingredients = mongo_response1[0]['ingredientNames']

        # flash('Recipes Found','success')
        return redirect(url_for('retrieved_recipes', ingredients=selected_ingredients))

    videoTitles = db.videos.distinct("title")
    return render_template('enter_recipe.html', videos=videoTitles)

@app.route('/enter_ingredients', methods=['GET','POST'])
def enter_ingredients():
    if request.method == 'POST':
        selected_ingredients = request.form.getlist('ingredient')
        
        try:
            if session['logged_in']:
                db.users.update_one({ "username" : "janethuangg" },{ "$set": {"pantry":selected_ingredients }})
        except: 
            pass

        # flash('Recipes Found','success')
        return redirect(url_for('retrieved_recipes', ingredients=selected_ingredients))

    ingredients = db.ingredients.distinct('name')
    pantry = []
    try:
        if session['logged_in']:
            pantry = db.users.find_one({"username":"janethuangg"},{"_id":0,"pantry":1})['pantry']
    except:
        pass

    return render_template('enter_ingredients.html', ingredients=ingredients, pantry=pantry)

@app.route('/top_ingredients')
def top_ingredients():
    mongo_response = db.ingredients.find({},{'_id':0,'name':1, 'count':1}).sort([("count", -1), ("name", 1)]).limit(10)
    num_videos = db.videos.count_documents({})

    ordered_ingredients = []
    for x in mongo_response:
        x['count'] = round((x['count']/num_videos)*100,1)
        ordered_ingredients.append(x)

    return render_template('top_ingredients.html', ingredients=ordered_ingredients)  

@app.route('/retrieved_recipes', methods=['GET','POST'])
def retrieved_recipes():
    if request.method == 'POST':
        final_recipes = request.form.getlist('final_recipe')
        return redirect(url_for('final_recipes', recipe_ids=final_recipes))

    selected_ingredients = request.args.getlist('ingredients')
    retrieved_recipes = list(db.videos.find({"ingredientNames": {"$not": {"$elemMatch": {"$nin" : selected_ingredients }}}},{ "id": 1, "ingredientDetails":1,"_id":0,"title":1}))
    
    # retrieved_recipes = []
    # for x in mongo_response:
    #     retrieved_recipes.append(x)

    # for i in range(len(retrieved_recipes)):
    #     retrieved_recipes[i] = json.loads(retrieved_recipes[i].replace("'", '"'))

    return render_template('retrieved_recipes.html', recipes=retrieved_recipes)

@app.route('/final_recipes')
def final_recipes():
    ids = request.args.getlist('recipe_ids')
    final_recipes = list(db.videos.find({"id":{"$in":ids}}))
    
    # final_recipes = []
    # for x in mongo_response:
    #     final_recipes.append(x)

    # for i in range(len(final_recipes)):
    #     final_recipes[i] = json.loads(final_recipes[i].replace("'", '"'))
        
    compiled = {}
    for recipe in final_recipes:
        ingredientDetails = recipe['ingredientDetails']
        for key,value in ingredientDetails.items():
            if key not in compiled.keys():
                compiled[key] = copy.deepcopy(value)
            else:
                for unit in value.keys():
                    try:
                        compiled[key][unit] += value[unit]
                    except:
                        compiled[key][unit] = value[unit]       

    return render_template('final_recipes.html', recipes=final_recipes, compiled=compiled)

if __name__ == '__main__':
    app.run(debug=True)