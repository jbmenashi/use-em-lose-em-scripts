from pymongo import MongoClient
from bson import ObjectId
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])
db = client.ff_db
player_projections = db["PlayerProjections"]

projection_checks = [
    {"game_date": "2023-APR-03", "projection_week": 1},
    {"game_date": "2023-APR-04", "projection_week": 1},
    {"game_date": "2023-APR-05", "projection_week": 1},
    {"game_date": "2023-APR-06", "projection_week": 1},
    {"game_date": "2023-APR-07", "projection_week": 1},
    {"game_date": "2023-APR-08", "projection_week": 1},
    {"game_date": "2023-APR-09", "projection_week": 1},
    {"game_date": "2023-APR-10", "projection_week": 2},
    {"game_date": "2023-APR-11", "projection_week": 2},
    {"game_date": "2023-APR-12", "projection_week": 2},
    {"game_date": "2023-APR-13", "projection_week": 2},
    {"game_date": "2023-APR-14", "projection_week": 2},
    {"game_date": "2023-APR-15", "projection_week": 2},
    {"game_date": "2023-APR-16", "projection_week": 2},
]



def get_player_projections():
    for proj in projection_checks:
        res = requests.get(f"https://api.sportsdata.io/v3/mlb/projections/json/PlayerGameProjectionStatsByDate/{proj['game_date']}?key=e83af77dbf8849018751c5366a98e164")

        projection_inserts = []

        for player in res.json():
            if projection_exists := player_projections.find_one({
                    "player_id": player["PlayerID"],
                    "game_date": proj["game_date"]
                }) is not None:
                found_projection = player_projections.find_one({
                    "player_id": player["PlayerID"],
                    "game_date": proj["game_date"]
                })
                update = 0
                if found_projection["hits"] != player["Hits"]:
                    update = 1
                if found_projection["home_runs"] != player["HomeRuns"]:
                    update = 1
                if found_projection["runs_batted_in"] != player["RunsBattedIn"]:
                    update = 1    

                if update == 1:
                    player_projections.update_one(
                        {"_id": ObjectId(found_projection["_id"])},
                        {"$set": {
                            "hits": player["Hits"],
                            "home_runs": player["HomeRuns"],
                            "runs_batted_in": player["RunsBattedIn"]
                        }}
                    )       
                    print(f"updated projection for {player["Name"]} for game_date {proj["game_date"]}")
                else:
                    print(f"no projection change for {player["Name"]} for game_date {proj["game_date"]}")
                        
            else:
                if player["PositionCategory"] != "P":
                    projection = {}
                    projection["player_id"] = player["PlayerID"]
                    projection["player_name"] = player["Name"]
                    projection["team_id"] = player["TeamID"]
                    projection["team_abbv"] = player["Team"]
                    projection["game_date"] = proj['game_date']
                    projection["week"] = proj['projection_week']
                    projection["opponent"] = player["Opponent"]
                    projection["opponent_team_id"] = player["OpponentID"]
                    projection["location"] = player["HomeOrAway"]
                    # if player["isGameOver"]:
                    #     game_log["active"] = False
                    # else:
                    #     game_log["active"] = True
                    projection["hits"] = player["Hits"]
                    projection["home_runs"] = player["HomeRuns"]
                    projection["runs_batted_in"] = player["RunsBattedIn"]
                    projection_inserts.append(projection)
                    
                    print(f"inserted new projection for {player["Name"]} for game_date {proj["game_date"]}")

        if len(projection_inserts) > 0:
            player_projections.insert_many(projection_inserts)

    return

get_player_projections()