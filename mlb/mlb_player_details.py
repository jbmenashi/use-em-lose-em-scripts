from pymongo import MongoClient
from bson import ObjectId
import requests
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])
db = client.ff_db
playerDetails = db["PlayerDetails"]

def get_player_details():
    docs = []

    res = requests.get("https://api.sportsdata.io/v3/mlb/scores/json/Players?key=e83af77dbf8849018751c5366a98e164")

    for player in res.json():
        if player_exists := playerDetails.find_one({"player_id": player["PlayerID"]}) is not None:
            found_player = playerDetails.find_one({"player_id": player["PlayerID"]}) 
            update = 0
            if found_player["first_name"] != player["FirstName"]:
                update = 1
            if found_player["last_name"] != player["LastName"]:
                update = 1
            if found_player["status"] != player["Status"]:
                update = 1
            if found_player["team_id"] != player["TeamID"]:
                update = 1
            if found_player["team_abbreviation"] != player["Team"]:
                update = 1
            if found_player["jersey_num"] != player["Jersey"]:
                update = 1
            if found_player["position_category"] != player["PositionCategory"]:
                update = 1
            if found_player["position"] != player["Position"]:
                update = 1

            if update == 1:
                playerDetails.update_one(
                    {"_id": ObjectId(found_player["_id"])},
                    {"$set": {
                        "first_name": player["FirstName"],
                        "last_name": player["LastName"],
                        "status": player["Status"],
                        "team_id": player["TeamID"],
                        "team_abbreviation": player["Team"],
                        "jersey_num": player["Jersey"],
                        "position_category": player["PositionCategory"],
                        "position": player["Position"],
                    }}
                )       
                print(f"updated {player["FirstName"]} {player["LastName"]}")
        else:
            if player["Status"] != "Minors" and player["PositionCategory"] != "P":
                doc = {}
                doc["sport"] = "MLB"
                doc["player_id"] = player["PlayerID"]
                doc["first_name"] = player["FirstName"]
                doc["last_name"] = player["LastName"]
                doc["status"] = player["Status"]
                doc["team_id"] = player["TeamID"]
                doc["team_abbreviation"] = player["Team"]
                doc["jersey_num"] = player["Jersey"]
                doc["position_category"] = player["PositionCategory"]
                doc["position"] = player["Position"]
                docs.append(doc)
                print(f"inserted {player["FirstName"]} {player["LastName"]}")

    if len(docs) > 0:
        playerDetails.insert_many(docs) 

get_player_details()