from pymongo import MongoClient
from bson import ObjectId
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])
db = client.uele2

matchups = db["matchups"]
leagues = db["leagues"]
contestants = db["contestants"]

def update_standings():
    # get all leagues that are active
    active_leagues = leagues.find({"active": True})

    for league in active_leagues:
        # in each league, get all matchups that are finished
        finished_matchups = list(matchups.find({"leagueId": ObjectId(league["_id"]), "finished": True, "seasonType": "REG"}))
        # and get all the contestants
        league_contestants = list(contestants.find({"leagueId": ObjectId(league["_id"])}))

        for contestant in league_contestants:
            con_standings = {
                "wins": 0,
                "losses": 0,
                "winPct": 0,
                "totalPointsFor": 0,
                "totalPointsAg": 0
            }
            filtered_matchups = list(filter(lambda finished_matchups: finished_matchups['team1Id'] == contestant["_id"] or finished_matchups['team2Id'] == contestant["_id"], finished_matchups))
            for matchup in filtered_matchups:
                if matchup["winner"] == contestant["_id"]:
                    con_standings["wins"] += 1
                else:
                    con_standings["losses"] += 1

                if matchup["team1Id"] == contestant["_id"]:
                    con_standings["totalPointsFor"] += matchup["team1Score"]
                    con_standings["totalPointsAg"] += matchup["team2Score"]
                else:
                    con_standings["totalPointsFor"] += matchup["team2Score"]
                    con_standings["totalPointsAg"] += matchup["team1Score"]

            con_standings["winPct"] = float(con_standings["wins"] / (con_standings["wins"] + con_standings["losses"]))
            contestants.update_one(
            {"_id": ObjectId(contestant["_id"])},
            {"$set": {
                "standings": con_standings
            }}
        )  
                    



update_standings()