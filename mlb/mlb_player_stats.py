from pymongo import MongoClient
from bson import ObjectId
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
from collections import defaultdict

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])

gameDate = "2023-APR-02"
current_week = 1
current_season = 2023

db = client.uele2
player_game_logs = db["playergamelogs"]
#player_season_stats = db["playerseasonstats"]
lineups = db["lineups"]
leagues = db["leagues"]

game_log_inserts = []

def get_player_game_logs():
    res = requests.get(f"https://api.sportsdata.io/v3/mlb/stats/json/PlayerGameStatsByDate/{gameDate}?key=e83af77dbf8849018751c5366a98e164")

    updated_players = []

    for player in res.json():
        if game_log_exists := player_game_logs.find_one({
                "playerId": player["PlayerID"],
                "gameDate": gameDate
            }) is not None:
            found_game_log = player_game_logs.find_one({
                "playerId": player["PlayerID"],
                "gameDate": gameDate
            })
            update = 0
            if found_game_log["hits"] != player["Hits"]:
                update = 1
            if found_game_log["homeRuns"] != player["HomeRuns"]:
                update = 1
            if found_game_log["runsBattedIn"] != player["RunsBattedIn"]:
                update = 1    

            if update == 1:
                player_game_logs.update_one(
                    {"_id": ObjectId(found_game_log["_id"])},
                    {"$set": {
                        "hits": player["Hits"],
                        "homeRuns": player["HomeRuns"],
                        "runsBattedIn": player["RunsBattedIn"]
                    }}
                )       
                print(f"updated {player["Name"]}")
                updated_players.append(player["PlayerID"])
            else:
                print(f"no change for {player["Name"]}")
                    
        else:
            if player["PositionCategory"] != "P":
                game_log = {}
                game_log["playerId"] = player["PlayerID"]
                game_log["playerName"] = player["Name"]
                game_log["teamId"] = player["TeamID"]
                game_log["teamAbbv"] = player["Team"]
                game_log["gameDate"] = gameDate
                # if player["isGameOver"]:
                #     game_log["active"] = False
                # else:
                #     game_log["active"] = True
                game_log["hits"] = player["Hits"]
                game_log["homeRuns"] = player["HomeRuns"]
                game_log["runsBattedIn"] = player["RunsBattedIn"]
                game_log_inserts.append(game_log)
                
                print(f"inserted new game log for {player["Name"]}")
                updated_players.append(player["PlayerID"])

    if len(game_log_inserts) > 0:
        player_game_logs.insert_many(game_log_inserts)

    return(updated_players)

# def season_stats(playerIds):
#     new_season_stats = []
#     for updated_playerId in playerIds:
#         result = db['playergamelogs'].aggregate([
#             {
#                 '$match': {
#                     'playerId': updated_playerId
#                 }
#             }, {
#                 '$group': {
#                     '_id': '$playerId', 
#                     'totalHits': {
#                         '$sum': '$hits'
#                     },
#                     'totalHomeRuns': {
#                         '$sum': '$homeRuns'
#                     },
#                     'totalRunsBattedIn': {
#                         '$sum': '$runsBattedIn'
#                     }
#                 }
#             }
#         ])

#         result_obj = list(result)[0]

#         if season_stat_exists := player_season_stats.find_one({
#             "playerId": updated_playerId,
#             "season": current_season
#             }) is not None:
#                 found_season_stat = player_season_stats.find_one({
#                 "playerId": updated_playerId,
#                 "season": current_season
#                 })
#                 player_season_stats.update_one(
#                     {"_id": ObjectId(found_season_stat["_id"])},
#                     {"$set": {
#                         "stats.hits": result_obj["totalHits"],
#                         "stats.homeRuns": result_obj["totalHomeRuns"],
#                         "stats.runsBattedIn": result_obj["totalRunsBattedIn"]
#                     }}
#                 )       
#                 print(f"updated season stats for player {updated_playerId}")           
#         else:
#             season_stats = {}
#             season_stats["playerId"] = updated_playerId
#             season_stats["season"] = current_season
#             season_stats["stats"] = {}
#             season_stats["stats"]["hits"] = result_obj["totalHits"]
#             season_stats["stats"]["homeRuns"] = result_obj["totalHomeRuns"]
#             season_stats["stats"]["runsBattedIn"] = result_obj["totalRunsBattedIn"]
#             new_season_stats.append(season_stats)
#             print(f"Inserting new season stats for player {updated_playerId}")
    
#     if len(new_season_stats) > 0:
#         player_season_stats.insert_many(new_season_stats)

def update_lineups(playerIds):
    # iterate through list of player IDs
    for player in playerIds:
        print(f"checking lineups for player {player}")
        game_log = player_game_logs.find_one({"gameDate": gameDate, "playerId": player})
    # find lineups with that player Id and matches current week
        found_lineups = lineups.find({"selections.playerId": player, "week": current_week})

        for lineup in found_lineups:
            print(f"found selection for {player} in lineup {lineup["_id"]}")
            league = leagues.find_one({"_id": ObjectId(lineup["leagueId"])})
            style = league["style"]
            scoring = league["scoring"]["statistics"]

            game_log_league_specific = {}
            game_log_league_specific["gameDate"] = game_log["gameDate"]
            for k, v in scoring.items():
                game_log_league_specific[k] = game_log[k] * v

            selection_index = next((i for i, item in enumerate(lineup["selections"]) if item["playerId"] == player))

            if "gameLogs" not in lineup["selections"][selection_index].keys():
                print("first game log for player")
                stats_dict = { k:v for (k,v) in game_log_league_specific.items() if k != "gameDate"}
                lineups.update_one(
                    {"_id": ObjectId(lineup["_id"])},
                    {
                        "$push": { f"selections.{selection_index}.gameLogs": game_log_league_specific },
                        "$set": {
                            f"selections.{selection_index}.locked": True,
                            f"selections.{selection_index}.totalStats": stats_dict
                        }
                    }
                )
            else:
                stats_dict = defaultdict(int)

                game_log_exists = next((item for i, item in enumerate(lineup["selections"][selection_index]["gameLogs"]) if item["gameDate"] == gameDate), None)

                if game_log_exists:
                    print("game log for player updated")
                    for game_log in lineup["selections"][selection_index]["gameLogs"]:
                        if game_log["gameDate"] != game_log_league_specific["gameDate"]:
                            for key, value in game_log.items():
                                if key != "gameDate":
                                    stats_dict[key] += value

                    for key, value in game_log_league_specific.items():
                        if key != "gameDate":
                            stats_dict[key] += value

                    lineups.update_one(
                        {"_id": ObjectId(lineup["_id"])},
                        { "$pull": { f"selections.{selection_index}.gameLogs": { "gameDate": gameDate}}}
                    )
                    lineups.update_one(
                        {"_id": ObjectId(lineup["_id"])},
                        {
                            "$push": { f"selections.{selection_index}.gameLogs": game_log_league_specific },
                            "$set": { f"selections.{selection_index}.totalStats": stats_dict }
                        }
                    )
                else:
                    print("new game log for player")
                    for existing_game_logs in lineup["selections"][selection_index]["gameLogs"]:
                        for key, value in existing_game_logs.items():
                            if key != "gameDate":
                                stats_dict[key] += value

                    for key, value in game_log_league_specific.items():
                        if key != "gameDate":
                            stats_dict[key] += value

                    lineups.update_one(
                        {"_id": ObjectId(lineup["_id"])},
                        {
                            "$push": { f"selections.{selection_index}.gameLogs": game_log_league_specific },
                            "$set": {
                                    f"selections.{selection_index}.locked": True,
                                    f"selections.{selection_index}.totalStats": stats_dict
                                }
                        }
                    )
    
            # create/update keys in outcome field
            if style == 'Rotisserie':
                outcome_dict = {}
                for key,value in game_log_league_specific.items():
                    if key != "gameDate":
                        outcome_dict[f"outcome.{key}"] = {
                            "$sum": f"$selections.totalStats.{key}"
                        }

                result = list(lineups.aggregate([
                    {
                        '$match': {
                            '_id': ObjectId(lineup["_id"])
                        }
                    }, {
                        '$set': outcome_dict
                    }
                ]))

                lineups.update_one(
                    {"_id": ObjectId(lineup["_id"])},
                    {
                        "$set": { 
                                f"outcome": result[0]["outcome"]
                            }
                    }
                )   
                print("updated outcome")
    return

players = get_player_game_logs()
#season_stats(players)
#players = [10002076]
update_lineups(players)

