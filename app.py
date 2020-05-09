from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
from pymongo import MongoClient
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_paginate import Pagination, get_page_parameter, get_page_args
import json
import os
import copy
import math
from passlib.hash import sha256_crypt

# MongoDB Config
client = MongoClient(os.environ.get('MONGO_URI'))
db = client.desserts
 
 # App Setup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Decorator function to restrict access to certain pages
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized - Please log in', 'danger')
            return redirect(url_for('login'))
    return wrap
    
# Registration form class
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

        try:        
            mongo_response1 = db.videos.find({"title":selected_video})
            selected_ingredients = mongo_response1[0]['ingredientNames']
            return redirect(url_for('retrieved_recipes', ingredients=selected_ingredients))
        except:
            flash('Invalid video','danger')
            return redirect(url_for('enter_recipe'))

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

def get_recipes(offset=0, per_page=10, recipes=[]):
    return recipes[offset: offset + per_page]

def formatName(recipe):
    if len(recipe['title'])>55:
        recipe['title'] = recipe['title'][:55]+"..." 
    return recipe

@app.route('/video_library')
def video_library():
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    recipes = list(db.videos.find({},{ "id": 1, "ingredientDetails":1,"_id":0,"title":1}).sort([("title",1)]))
    recipes = list(map(formatName,recipes))
    total = len(recipes)

    pagination_recipes = get_recipes(offset=offset, per_page=per_page, recipes=recipes)
    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4')

    return render_template('library.html', 
                            recipes=pagination_recipes,
                            page=page,
                            per_page=per_page,
                            pagination=pagination)

@app.route('/retrieved_recipes', methods=['GET','POST'])
def retrieved_recipes():
    if request.method == 'POST':
        final_recipes = request.form.getlist('final_recipe')
        return redirect(url_for('final_recipes', recipe_ids=final_recipes))

    selected_ingredients = request.args.getlist('ingredients')
    recipes = list(db.videos.find({"ingredientNames": {"$not": {"$elemMatch": {"$nin" : selected_ingredients }}}},{ "id": 1, "ingredientDetails":1,"_id":0,"title":1}).sort([("title", 1)]))
    recipes = list(map(formatName,recipes))
    print(recipes[:5])
    return render_template('retrieved_recipes.html',recipes=recipes)

@app.route('/final_recipes')
def final_recipes():
    ids = request.args.getlist('recipe_ids')
    final_recipes = list(db.videos.find({"id":{"$in":ids}}))
    final_recipes = list(map(formatName,final_recipes))
        
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