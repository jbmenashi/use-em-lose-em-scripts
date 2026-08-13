from pymongo import MongoClient
from bson import ObjectId
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])
db = client.uele2
player_projections = db["playerprojections"]

projection_checks = [
    {"gameDate": "2023-APR-03", "projection_week": 1},
    {"gameDate": "2023-APR-04", "projection_week": 1},
    {"gameDate": "2023-APR-05", "projection_week": 1},
    {"gameDate": "2023-APR-06", "projection_week": 1},
    {"gameDate": "2023-APR-07", "projection_week": 1},
    {"gameDate": "2023-APR-08", "projection_week": 1},
    {"gameDate": "2023-APR-09", "projection_week": 1},
    {"gameDate": "2023-APR-10", "projection_week": 2},
    {"gameDate": "2023-APR-11", "projection_week": 2},
    {"gameDate": "2023-APR-12", "projection_week": 2},
    {"gameDate": "2023-APR-13", "projection_week": 2},
    {"gameDate": "2023-APR-14", "projection_week": 2},
    {"gameDate": "2023-APR-15", "projection_week": 2},
    {"gameDate": "2023-APR-16", "projection_week": 2},
]



def get_player_projections():
    for proj in projection_checks:
        res = requests.get(f"https://api.sportsdata.io/v3/mlb/projections/json/PlayerGameProjectionStatsByDate/{proj['gameDate']}?key=e83af77dbf8849018751c5366a98e164")

        projection_inserts = []

        for player in res.json():
            if projection_exists := player_projections.find_one({
                    "playerId": player["PlayerID"],
                    "gameDate": proj["gameDate"]
                }) is not None:
                found_projection = player_projections.find_one({
                    "playerId": player["PlayerID"],
                    "gameDate": proj["gameDate"]
                })
                update = 0
                if found_projection["hits"] != player["Hits"]:
                    update = 1
                if found_projection["homeRuns"] != player["HomeRuns"]:
                    update = 1
                if found_projection["runsBattedIn"] != player["RunsBattedIn"]:
                    update = 1    

                if update == 1:
                    player_projections.update_one(
                        {"_id": ObjectId(found_projection["_id"])},
                        {"$set": {
                            "hits": player["Hits"],
                            "homeRuns": player["HomeRuns"],
                            "runsBattedIn": player["RunsBattedIn"]
                        }}
                    )       
                    print(f"updated projection for {player["Name"]} for gameDate {proj["gameDate"]}")
                else:
                    print(f"no projection change for {player["Name"]} for gameDate {proj["gameDate"]}")
                        
            else:
                if player["PositionCategory"] != "P":
                    projection = {}
                    projection["playerId"] = player["PlayerID"]
                    projection["playerName"] = player["Name"]
                    projection["teamId"] = player["TeamID"]
                    projection["teamAbbv"] = player["Team"]
                    projection["gameDate"] = proj['gameDate']
                    projection["week"] = proj['projection_week']
                    projection["opponent"] = player["Opponent"]
                    projection["opponentTeamId"] = player["OpponentID"]
                    projection["location"] = player["HomeOrAway"]
                    # if player["isGameOver"]:
                    #     game_log["active"] = False
                    # else:
                    #     game_log["active"] = True
                    projection["hits"] = player["Hits"]
                    projection["homeRuns"] = player["HomeRuns"]
                    projection["runsBattedIn"] = player["RunsBattedIn"]
                    projection_inserts.append(projection)
                    
                    print(f"inserted new projection for {player["Name"]} for gameDate {proj["gameDate"]}")

        if len(projection_inserts) > 0:
            player_projections.insert_many(projection_inserts)

    return

get_player_projections()