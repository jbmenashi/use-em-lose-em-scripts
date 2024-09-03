from pymongo import MongoClient
from bson import ObjectId
import requests
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])
db = client.ff_db
teams = db["Teams"]
playerDetails = db["PlayerDetails"]

def get_teams():
    team_docs = []
    team_defense_docs = []

    url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLTeams"

    querystring = {"sortBy":"teamID"}

    headers = {
        "x-rapidapi-key": os.environ["RAPID_API_KEY"],
        "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    res = requests.get(url, headers=headers, params=querystring)

    for team in res.json()["body"]:
        team_def_doc = {}
        team_def_doc["sport"] = "NFL"
        team_def_doc["player_id"] = int(team["teamID"])
        team_def_doc["team_id"] = int(team["teamID"])
        team_def_doc["player_name"] = team["teamAbv"] + " Defense"
        team_def_doc["status"] = "Active"
        team_def_doc["team_id"] = int(team["teamID"])
        team_def_doc["team_abbreviation"] = team["teamAbv"]
        team_def_doc["jersey_num"] = ""
        team_def_doc["position"] = "DEF"
        team_def_doc["logo"] = team["nflComLogo1"]
        team_defense_docs.append(team_def_doc)

        team_doc = {}
        team_doc["sport"] = "NFL"
        team_doc["team_id"] = int(team["teamID"])
        team_doc["city"] = team["teamCity"]
        team_doc["nickname"] = team["teamName"]
        team_doc["abbreviation"] = team["teamAbv"]
        team_doc["subleague"] = team["conferenceAbv"]
        team_doc["division"] = team["division"]
        team_doc["logo"] = team["nflComLogo1"]
        team_docs.append(team_doc)

    if len(team_defense_docs) > 0:
        playerDetails.insert_many(team_defense_docs) 
        teams.insert_many(team_docs) 

get_teams()