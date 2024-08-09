from pymongo import MongoClient
from bson import ObjectId
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_CONN"])
db = client.ff_db

matchups = db["Matchups"]
leagues = db["Leagues"]
contestants = db["Contestants"]

def update_standings():
    # get all leagues that are active
    active_leagues = leagues.find({"active": True})

    for league in active_leagues:
        # in each league, get all matchups that are finished
        finished_matchups = list(matchups.find({"league_id": ObjectId(league["_id"]), "finished": True, "season_type": "REG"}))
        # and get all the contestants
        league_contestants = list(contestants.find({"league_id": ObjectId(league["_id"])}))

        for contestant in league_contestants:
            con_standings = {
                "wins": 0,
                "losses": 0,
                "win_pct": 0,
                "total_points_for": 0,
                "total_points_ag": 0
            }
            filtered_matchups = list(filter(lambda finished_matchups: finished_matchups['team_1_id'] == contestant["_id"] or finished_matchups['team_2_id'] == contestant["_id"], finished_matchups))
            for matchup in filtered_matchups:
                if matchup["winner"] == contestant["_id"]:
                    con_standings["wins"] += 1
                else:
                    con_standings["losses"] += 1

                if matchup["team_1_id"] == contestant["_id"]:
                    con_standings["total_points_for"] += matchup["team_1_score"]
                    con_standings["total_points_ag"] += matchup["team_2_score"]
                else:
                    con_standings["total_points_for"] += matchup["team_2_score"]
                    con_standings["total_points_ag"] += matchup["team_1_score"]
            
            con_standings["win_pct"] = float(con_standings["wins"] / (con_standings["wins"] + con_standings["losses"]))
            contestants.update_one(
            {"_id": ObjectId(contestant["_id"])},
            {"$set": {
                "standings": con_standings
            }}
        )  
                    



update_standings()