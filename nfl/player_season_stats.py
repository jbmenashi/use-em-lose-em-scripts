from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])

current_season = 2024

db = client.uele2
player_season_stats = db["playerseasonstats"]

new_season_stats = []

def season_stats():
    result = list(db['nflgamelogs'].aggregate([
        {
            '$match': {
                'season': current_season
            }
        }, {
            '$group': {
                '_id': '$playerId', 
                'totalGames': {'$sum': 1},
                'totalPassYds': { '$sum': '$passYds' },
                'totalPassTds': { '$sum': '$passTds' },
                'totalInts': { '$sum': '$ints' },
                'totalRushYds': { '$sum': '$rushYds' },
                'totalReceptions': { '$sum': '$receptions' },
                'totalRecYds': { '$sum': '$recYds' },
                'totalFumbles': { '$sum': '$fumbles' },
                'totalTds': { '$sum': '$tds' },
                'totalTwoPtConv': { '$sum': '$twoPtConv' },
                'totalDefPtsAllowed': { '$sum': '$defPtsAllowed' },
                'totalDefSacks': { '$sum': '$defSacks' },
                'totalDefFumbleRec': { '$sum': '$defFumbleRec' },
                'totalDefInts': { '$sum': '$defInts' },
                'totalDefBlkKicks': { '$sum': '$defBlkKicks' },
                'totalDefSafeties': { '$sum': '$defSafeties' },
                'totalDefTdsScored': { '$sum': '$defTdsScored' },
                'totalYahooPts': { '$sum': '$yahooPts' }
            }
        }
    ]))

    for player in result:
        if season_stat_exists := player_season_stats.find_one({
            "playerId": player["_id"],
            "season": current_season
            }) is not None:
                found_season_stat = player_season_stats.find_one({
                "playerId": player["_id"],
                "season": current_season
                })
                player_season_stats.update_one(
                    {"_id": ObjectId(found_season_stat["_id"])},
                    {"$set": {
                        "stats.games": player["totalGames"],
                        "stats.passYds": player["totalPassYds"],
                        "stats.passTds": player["totalPassTds"],
                        "stats.ints": player["totalInts"],
                        "stats.rushYds": player["totalRushYds"],
                        "stats.receptions": player["totalReceptions"],
                        "stats.recYds": player["totalRecYds"],
                        "stats.fumbles": player["totalFumbles"],
                        "stats.tds": player["totalTds"],
                        "stats.twoPtConv": player["totalTwoPtConv"],
                        "stats.defPtsAllowed": player["totalDefPtsAllowed"],
                        "stats.defSacks": player["totalDefSacks"],
                        "stats.defFumbleRec": player["totalDefFumbleRec"],
                        "stats.defInts": player["totalDefInts"],
                        "stats.defBlkKicks": player["totalDefBlkKicks"],
                        "stats.defSafeties": player["totalDefSafeties"],
                        "stats.defTdsScored": player["totalDefTdsScored"],
                        "stats.yahooPts": player["totalYahooPts"]
                        }}
                    )       
                print(f"updated season stats for player {player['_id']}")           
        else:
            season_stats = {}
            season_stats["playerId"] = player['_id']
            season_stats["sport"] = "NFL"
            season_stats["season"] = current_season
            season_stats["stats"] = {}
            season_stats["stats"]["games"] = player["totalGames"]
            season_stats["stats"]["passYds"] = player["totalPassYds"]
            season_stats["stats"]["passTds"] = player["totalPassTds"]
            season_stats["stats"]["ints"] = player["totalInts"]
            season_stats["stats"]["rushYds"] = player["totalRushYds"]
            season_stats["stats"]["receptions"] = player["totalReceptions"]
            season_stats["stats"]["recYds"] = player["totalRecYds"]
            season_stats["stats"]["fumbles"] = player["totalFumbles"]
            season_stats["stats"]["tds"] = player["totalTds"]
            season_stats["stats"]["twoPtConv"] = player["totalTwoPtConv"]
            season_stats["stats"]["defPtsAllowed"] = player["totalDefPtsAllowed"]
            season_stats["stats"]["defSacks"] = player["totalDefSacks"]
            season_stats["stats"]["defFumbleRec"] = player["totalDefFumbleRec"]        
            season_stats["stats"]["defInts"] = player["totalDefInts"]        
            season_stats["stats"]["defBlkKicks"] = player["totalDefBlkKicks"]        
            season_stats["stats"]["defSafeties"] = player["totalDefSafeties"]        
            season_stats["stats"]["defTdsScored"] = player["totalDefTdsScored"]              
            season_stats["stats"]["yahooPts"] = player["totalYahooPts"]              
            new_season_stats.append(season_stats)
            print(f"Inserting new season stats for player {player['_id']}")
        
    if len(new_season_stats) > 0:
        player_season_stats.insert_many(new_season_stats)

season_stats()