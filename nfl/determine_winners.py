from pymongo import MongoClient
from bson import ObjectId
import requests
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])

current_week = 19
current_season = 2024

db = client.uele2
matchups = db["matchups"]

def determine_winners():
    found_matchups = matchups.find({"season": current_season, "week": current_week - 1, "finished": False})  
    
    for matchup in found_matchups:
        if matchup["team1Score"] > matchup["team2Score"]:
            matchups.update_one(
                {"_id": ObjectId(matchup["_id"])},
                {
                    "$set": {
                        "winner": ObjectId(matchup["team1Id"]),
                        "loser": ObjectId(matchup["team2Id"]),
                        "finished": True,
                    }
                }
            )
        else:
            matchups.update_one(
                {"_id": ObjectId(matchup["_id"])},
                {
                    "$set": {
                        "winner": ObjectId(matchup["team2Id"]),
                        "loser": ObjectId(matchup["team1Id"]),
                        "finished": True,
                    }
                }
            )
    return


determine_winners()

