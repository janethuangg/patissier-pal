from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
# from data import Articles
#https://stackoverflow.com/questions/52261686/issues-with-flask-mysqldb-using-python3-7?rq=1
#export DYLD_LIBRARY_PATH=/usr/local/mysql/lib/:$DYLD_LIBRARY_PATH
# from flask_ngrok import run_with_ngrok
from pymongo import MongoClient
import json
import copy

client = MongoClient("mongodb+srv://janet:janet@cluster0-nnw1z.mongodb.net/desserts?retryWrites=true&w=majority")
db = client.desserts
 
app = Flask(__name__)
# run_with_ngrok(app)  # Start ngrok when app is run

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/enter_recipe', methods=['GET','POST'])
def enter_recipe():
    if request.method == 'POST':
        selected_video = request.form.get('video')
        
        mongo_response1 = db.videos.find({"title":selected_video})
        selected_ingredients = mongo_response1[0]['ingredientNames']

        mongo_response2 = db.videos.find({"ingredientNames": {"$not": {"$elemMatch": {"$nin" : selected_ingredients }}}},{ "id": 1, "ingredientDetails":1,"_id":0,"title":1})
        retrieved_recipes = []
        for x in mongo_response2:
            retrieved_recipes.append(x)
        
        # flash('Recipes Found','success')
        return redirect(url_for('retrieved_recipes', recipes=retrieved_recipes))

    videoTitles = db.videos.distinct("title")
    return render_template('enter_recipe.html', videos=videoTitles)

@app.route('/enter_ingredients', methods=['GET','POST'])
def enter_ingredients():
    if request.method == 'POST':
        selected_ingredients = request.form.getlist('ingredient')
        mongo_response = db.videos.find({"ingredientNames": {"$not": {"$elemMatch": {"$nin" : selected_ingredients }}}},{ "id": 1, "ingredientDetails":1,"_id":0,"title":1})
        
        retrieved_recipes = []
        for x in mongo_response:
            retrieved_recipes.append(x)
        
        # flash('Recipes Found','success')
        return redirect(url_for('retrieved_recipes', recipes=retrieved_recipes))

    ingredients = db.ingredients.distinct('name')
    return render_template('enter_ingredients.html', ingredients=ingredients)

@app.route('/top_ingredients')
def top_ingredients():
    mongo_response = db.ingredients.find({},{'_id':0,'name':1, 'count':1}).sort([("count", -1), ("name", 1)]).limit(10)
    num_videos = db.videos.count()

    ordered_ingredients = []
    for x in mongo_response:
        x['count'] = round((x['count']/num_videos)*100,1)
        ordered_ingredients.append(x)

    return render_template('top_ingredients.html', ingredients=ordered_ingredients)  

@app.route('/retrieved_recipes', methods=['GET','POST'])
def retrieved_recipes():
    if request.method == 'POST':
        final_recipes = request.form.getlist('final_recipe')
        return redirect(url_for('final_recipes', recipes=final_recipes))

    retrieved_recipes = request.args.getlist('recipes')

    for i in range(len(retrieved_recipes)):
        retrieved_recipes[i] = json.loads(retrieved_recipes[i].replace("'", '"'))

    return render_template('retrieved_recipes.html', recipes=retrieved_recipes)

@app.route('/final_recipes')
def final_recipes():
    final_recipes = request.args.getlist('recipes')

    for i in range(len(final_recipes)):
        final_recipes[i] = json.loads(final_recipes[i].replace("'", '"'))
        
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
    app.secret_key='secret123'
    app.run(debug=True)