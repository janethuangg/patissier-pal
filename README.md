# Patissier Pal
deployed at https://patissier-pal.herokuapp.com/

## Project Overview
This project serves as a resource for bakers who prefer following YouTube videos to written recipes -- it aims to help them discover new recipes and reduce wasted ingredients.

## App Functionality
- **video library**: view the video library with embedded youtube videos alongside their ingredient lists
- **top ingredients**: check out the top 10 most used ingredients used across all 900+ videos in the database
---
- **start with the ingredients**: enter what ingredients you have to find out what you can make 
- **start with the recipe**: select a video from the index to see what other things you can make given the same ingredients
---
- **login**: create an account to save your ingredient selection (known as your "pantry") for next time
- **final recipes**: gather a compiled list of ingredients based on your final selected videos

## Project Structure
- *app.py* -- core module containing all routes & controllers
- *templates* folder -- contains all jinja templates
- *static* folder -- contains stylesheets & gifs
- *data* folder -- contains database population notebook + local files and authentication info used in the script
- *conf.py* & *Procfile* -- configuration files for Heroku deployment

## Database Population
- see *ingredient_parser.ipynb* under the data directory
- queries newly uploaded videos from the given youtube channels, parses out the ingredients from their descriptions, then pushes the new video-recipe data to the mongodb database


