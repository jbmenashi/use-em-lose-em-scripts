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

    url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLPlayerList"

    headers = {
        "x-rapidapi-key": os.environ["RAPID_API_KEY"],
        "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    res = requests.get(url, headers=headers)

    for player in res.json()["body"]:
        if player_exists := playerDetails.find_one({"player_id": int(player["playerID"])}) is not None:
            found_player = playerDetails.find_one({"player_id": int(player["playerID"])}) 
            update = 0
            if found_player["player_name"] != player["longName"]:
                update = 1
            if found_player["status"] != player["injury"]["designation"]:
                update = 1
            if found_player["team_id"] != int(player["teamID"]):
                update = 1
            if found_player["team_abbreviation"] != player["team"]:
                update = 1
            if found_player["jersey_num"] != player["jerseyNum"]:
                update = 1
            if found_player["position"] != player["pos"]:
                update = 1

            if update == 1:
                playerDetails.update_one(
                    {"_id": ObjectId(found_player["_id"])},
                    {"$set": {
                        "player_name": player["longName"],
                        "status": player["injury"]["designation"],
                        "team_id": player["teamID"],
                        "team_abbreviation": player["team"],
                        "jersey_num": player["jerseyNum"],
                        "position": player["pos"],
                    }}
                )       
                print(f"updated {player["longName"]}")
        else:
            if player["pos"] in ["QB", "RB", "WR", "TE", "FB"]:
                doc = {}
                doc["sport"] = "NFL"
                doc["player_id"] = int(player["playerID"])
                doc["player_name"] = player["longName"]
                doc["status"] = player["injury"]["designation"]
                doc["team_id"] = int(player["teamID"])
                doc["team_abbreviation"] = player["team"]
                doc["jersey_num"] = player["jerseyNum"]
                doc["position"] = player["pos"]
                if "espnHeadshot" in player.keys():
                    doc["logo"] = player["espnHeadshot"]
                else:
                    doc["logo"] = ""
                docs.append(doc)
                print(f"inserted {player["longName"]}")

    if len(docs) > 0:
        playerDetails.insert_many(docs) 

get_player_details()