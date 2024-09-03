from pymongo import MongoClient
from bson import ObjectId
import requests
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])

current_week = 2
current_season = 2024

db = client.ff_db
matchups = db["Matchups"]

def determine_winners():
    found_matchups = matchups.find({"season": current_season, "week": current_week - 1, "finished": False})  
    
    for matchup in found_matchups:
        if matchup["team_1_score"] > matchup["team_2_score"]:
            matchups.update_one(
                {"_id": ObjectId(matchup["_id"])},
                {
                    "$set": { 
                        "winner": ObjectId(matchup["team_1_id"]),
                        "loser": ObjectId(matchup["team_2_id"]),
                        "finished": True,
                    }
                }
            ) 
        else:
            matchups.update_one(
                {"_id": ObjectId(matchup["_id"])},
                {
                    "$set": { 
                        "winner": ObjectId(matchup["team_2_id"]),
                        "loser": ObjectId(matchup["team_1_id"]),
                        "finished": True,
                    }
                }
            ) 
    return


determine_winners()

