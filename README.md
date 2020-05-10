# Patissier Pal
deployed at https://patissier-pal.herokuapp.com/

## App Functionality
- view the video library with embedded youtube videos alongside their ingredient lists
- check out the top 10 most used ingredients used across all 900+ videos in the database
- enter what ingredients you have to find out what you can make 
- create an account to save your ingredient selection (known as your "pantry") for next time
- select a video from the index to see what other things you can make given the same ingredients
- gather a compiled list of ingredients based on your final selected videos

## Database Population
- see *ingredient_parser.ipynb* under the data directory
- queries newly uploaded videos from the given youtube channels, parses out the ingredients from their descriptions, then pushes the new video-recipe data to the mongodb database




