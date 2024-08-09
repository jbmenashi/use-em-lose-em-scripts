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
lineups = db["Lineups"]

def generate_schedule():
    unscheduled_leagues = leagues.find({"scheduled": False, "full": True})
    for league in unscheduled_leagues:
        teams = league["size"]
        weeks = league["regular_season_weeks"]

        round_robin_cycle_length = teams - 1
        number_of_cycles = (weeks // round_robin_cycle_length) + 1
        matches = []
        half_size = teams // 2

        contestant_ids = []
        contestant_names = []
        league_contestants = contestants.find({"league_id": league["_id"]})
        for con in league_contestants:
            contestant_ids.append(con["_id"])
            contestant_names.append(con["team_name"])

        team_list = list(range(teams))
        week = 1

        for cycle in range(number_of_cycles):
            for round in range(round_robin_cycle_length):
                round_matches = []
                for i in range(half_size):
                    doc = {}
                    doc["league_id"] = league["_id"]
                    doc["season"] = league["season"]
                    doc["week"] = week
                    doc["season_type"] = "REG"
                    doc["team_1_id"] = contestant_ids[i]
                    doc["team_1_name"] = contestant_names[i]
                    doc["team_1_score"] = 0
                    doc["team_2_id"] = contestant_ids[-i-1]
                    doc["team_2_name"] = contestant_names[-i-1]
                    doc["team_2_score"] = 0
                    doc["winner"] = None
                    doc["loser"] = None
                    doc["finished"] = False
                    matchups.insert_one(doc)

                    lineup_one = {}
                    lineup_one["contestant_id"] = contestant_ids[i]
                    lineup_one["league_id"] = league["_id"]
                    lineup_one["sport"] = league["sport"]
                    lineup_one["style"] = league["style"]
                    lineup_one["season"] = league["season"]
                    lineup_one["week"] = week
                    lineup_one["score"] = 0
                    lineup_one["locked"] = False

                    lineup_one_selections = []
                    for key, value in league["roster"]["positions"].items():
                        lineup_one_selections.extend([key] * value)
                    
                    lineup_one_selections = [{"position": item.upper(), "locked": False, "index": index} for index, item in enumerate(lineup_one_selections)]
                    lineup_one["selections"] = lineup_one_selections
                    lineups.insert_one(lineup_one)

                    lineup_two = {}
                    lineup_two["contestant_id"] = contestant_ids[-i-1]
                    lineup_two["league_id"] = league["_id"]
                    lineup_two["sport"] = league["sport"]
                    lineup_two["style"] = league["style"]
                    lineup_two["season"] = league["season"]
                    lineup_two["week"] = week
                    lineup_two["score"] = 0
                    lineup_two["locked"] = False

                    lineup_two_selections = []
                    for key, value in league["roster"]["positions"].items():
                        lineup_two_selections.extend([key] * value)
                    
                    lineup_two_selections = [{"position": item, "locked": False, "index": index} for index, item in enumerate(lineup_two_selections)]
                    lineup_two["selections"] = lineup_two_selections
                    lineups.insert_one(lineup_two)


                contestant_ids.insert(1, contestant_ids.pop())
                contestant_names.insert(1, contestant_names.pop())

                week = week + 1
                if week > weeks:
                    break
                
        # # update league schedule bool
        leagues.update_one(
            {"_id": ObjectId(league["_id"])},
            {"$set": {
                "scheduled": True
            }}
        )  

        return "schedule generated"

generate_schedule()