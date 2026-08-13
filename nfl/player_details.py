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

    url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLPlayerList"

    headers = {
        "x-rapidapi-key": os.environ["RAPID_API_KEY"],
        "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    res = requests.get(url, headers=headers)

    for player in res.json()["body"]:
        if player_exists := playerDetails.find_one({"playerId": int(player["playerID"])}) is not None:
            found_player = playerDetails.find_one({"playerId": int(player["playerID"])})
            update = 0
            if found_player["playerName"] != player["longName"]:
                update = 1
            if found_player["status"] != player["injury"]["designation"]:
                update = 1
            if found_player["teamId"] != int(player["teamID"]):
                update = 1
            if found_player["teamAbbreviation"] != player["team"]:
                update = 1
            if found_player["jerseyNum"] != player["jerseyNum"]:
                update = 1
            if found_player["position"] != player["pos"]:
                update = 1

            if update == 1:
                playerDetails.update_one(
                    {"_id": ObjectId(found_player["_id"])},
                    {"$set": {
                        "playerName": player["longName"],
                        "status": player["injury"]["designation"],
                        "teamId": player["teamID"],
                        "teamAbbreviation": player["team"],
                        "jerseyNum": player["jerseyNum"],
                        "position": player["pos"],
                    }}
                )
                print(f"updated {player['longName']}")
        else:
            if player["pos"] in ["QB", "RB", "WR", "TE", "FB"]:
                doc = {}
                doc["sport"] = "NFL"
                doc["playerId"] = int(player["playerID"])
                doc["playerName"] = player["longName"]
                doc["status"] = player["injury"]["designation"]
                doc["teamId"] = int(player["teamID"])
                doc["teamAbbreviation"] = player["team"]
                doc["jerseyNum"] = player["jerseyNum"]
                doc["position"] = player["pos"]
                if "espnHeadshot" in player.keys():
                    doc["logo"] = player["espnHeadshot"]
                else:
                    doc["logo"] = ""
                docs.append(doc)
                print(f"inserted {player['longName']}")

    if len(docs) > 0:
        playerDetails.insert_many(docs) 

get_player_details()