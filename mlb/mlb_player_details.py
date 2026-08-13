from pymongo import MongoClient
from bson import ObjectId
import requests
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])
db = client.uele2
playerDetails = db["playerdetails"]

def get_player_details():
    docs = []

    res = requests.get("https://api.sportsdata.io/v3/mlb/scores/json/Players?key=e83af77dbf8849018751c5366a98e164")

    for player in res.json():
        if player_exists := playerDetails.find_one({"playerId": player["PlayerID"]}) is not None:
            found_player = playerDetails.find_one({"playerId": player["PlayerID"]})
            update = 0
            if found_player["firstName"] != player["FirstName"]:
                update = 1
            if found_player["lastName"] != player["LastName"]:
                update = 1
            if found_player["status"] != player["Status"]:
                update = 1
            if found_player["teamId"] != player["TeamID"]:
                update = 1
            if found_player["teamAbbreviation"] != player["Team"]:
                update = 1
            if found_player["jerseyNum"] != player["Jersey"]:
                update = 1
            if found_player["positionCategory"] != player["PositionCategory"]:
                update = 1
            if found_player["position"] != player["Position"]:
                update = 1

            if update == 1:
                playerDetails.update_one(
                    {"_id": ObjectId(found_player["_id"])},
                    {"$set": {
                        "firstName": player["FirstName"],
                        "lastName": player["LastName"],
                        "status": player["Status"],
                        "teamId": player["TeamID"],
                        "teamAbbreviation": player["Team"],
                        "jerseyNum": player["Jersey"],
                        "positionCategory": player["PositionCategory"],
                        "position": player["Position"],
                    }}
                )
                print(f"updated {player["FirstName"]} {player["LastName"]}")
        else:
            if player["Status"] != "Minors" and player["PositionCategory"] != "P":
                doc = {}
                doc["sport"] = "MLB"
                doc["playerId"] = player["PlayerID"]
                doc["firstName"] = player["FirstName"]
                doc["lastName"] = player["LastName"]
                doc["status"] = player["Status"]
                doc["teamId"] = player["TeamID"]
                doc["teamAbbreviation"] = player["Team"]
                doc["jerseyNum"] = player["Jersey"]
                doc["positionCategory"] = player["PositionCategory"]
                doc["position"] = player["Position"]
                docs.append(doc)
                print(f"inserted {player["FirstName"]} {player["LastName"]}")

    if len(docs) > 0:
        playerDetails.insert_many(docs) 

get_player_details()