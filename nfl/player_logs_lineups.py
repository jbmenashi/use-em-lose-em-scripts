from pymongo import MongoClient
from bson import ObjectId
import requests
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])

current_week = 16
current_season = 2024

db = client.ff_db
nfl_game_logs = db["NFLGameLogs"]
lineups = db["Lineups"]
leagues = db["Leagues"]
matchups = db["Matchups"]
games = db["Games"]

def get_nested(d, keys, default=0):
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d

game_log_inserts = []

def get_games():
    schedule_url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLGamesForWeek"

    schedule_querystring = {"week":f"{current_week}","seasonType":"reg","season":f"{current_season}"}

    schedule_headers = {
        "x-rapidapi-key": os.environ["RAPID_API_KEY"],
        "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    schedule_res = requests.get(schedule_url, headers=schedule_headers, params=schedule_querystring)
    for game in schedule_res.json()["body"]:
        if game_exists := games.find_one({
                "game_id": game["gameID"],
                "season": current_season,
                "week": current_week
            }) is not None:
            found_game = games.find_one({
                 "game_id": game["gameID"],
                "season": current_season,
                "week": current_week
            })

            if game["gameStatus"] != "Scheduled" and found_game["locked"] == False:
                games.update_one(
                    {"_id": ObjectId(found_game["_id"])},
                    {"$set": {
                        "locked": True
                    }}
                )  
                print(f"locked game {game['gameID']}")  
            else:
                print(f"{game['gameID']} not updated")
        else:
            new_game = {}
            new_game["game_id"] = game["gameID"]
            new_game["season"] = current_season
            new_game["week"] = current_week
            new_game["home_team_id"] = int(game["teamIDHome"])
            new_game["away_team_id"] = int(game["teamIDAway"])
            new_game["locked"] = False
            
            games.insert_one(new_game)
            print(f"inserted new game {game['gameID']}")
    return

def get_player_game_logs():
    updated_players = []
    locked_teams = []

    url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLGamesForWeek"

    querystring = {"week":f"{current_week}","seasonType":"reg","season":f"{current_season}"}

    headers = {
        "x-rapidapi-key": os.environ["RAPID_API_KEY"],
        "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    res = requests.get(url, headers=headers, params=querystring)

    for game in res.json()["body"]:
        game_id = game["gameID"]

        game_url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLBoxScore"

        game_querystring = {"gameID":f"{game_id}","fantasyPoints":"true","twoPointConversions":"2","passYards":".04","passAttempts":"0","passTD":"4","passCompletions":"0","passInterceptions":"-1","pointsPerReception":".5","carries":"0","rushYards":".1","rushTD":"6","fumbles":"-2","receivingYards":".1","receivingTD":"6","targets":"0","defTD":"6"}

        game_res = requests.get(game_url, headers=headers, params=game_querystring)

        box = game_res.json()["body"]
        if "gameStatus" in box.keys():
            if int(game["teamIDHome"]) not in locked_teams:
                locked_teams.append(int(game["teamIDHome"]))
                locked_teams.append(int(game["teamIDAway"]))
            print(game_id)
            for p in box["playerStats"]:
                player = box["playerStats"][p]
                if "Rushing" in player.keys() or "Passing" in player.keys() or "Receiving" in player.keys():

                    if game_log_exists := nfl_game_logs.find_one({
                            "player_id": int(player["playerID"]),
                            "season": current_season,
                            "week": current_week
                        }) is not None:
                        found_game_log = nfl_game_logs.find_one({
                            "player_id": int(player["playerID"]),
                            "season": current_season,
                            "week": current_week
                        })
                        update = 0
                        if found_game_log["pass_yds"] != int(get_nested(player, ["Passing", "passYds"])):
                            update = 1
                        if found_game_log["pass_tds"] != int(get_nested(player, ["Passing", "passTD"])):
                            update = 1
                        if found_game_log["ints"] != int(get_nested(player, ["Passing", "int"])):
                            update = 1    
                        if found_game_log["rush_yds"] != int(get_nested(player, ["Rushing", "rushYds"])):
                            update = 1     
                        if found_game_log["receptions"] != int(get_nested(player, ["Receiving", "receptions"])):
                            update = 1    
                        if found_game_log["rec_yds"] != int(get_nested(player, ["Receiving", "recYds"])):
                            update = 1    
                        if found_game_log["fumbles"] != int(get_nested(player, ["Defense", "fumblesLost"])):
                            update = 1   
                        if found_game_log["tds"] != int(get_nested(player, ["Rushing", "rushTD"])) + int(get_nested(player, ["Receiving", "recTD"])) + int(get_nested(player, ["Kicking", "kickReturnTD"])) + int(get_nested(player, ["Punting", "puntReturnTD"])):
                            update = 1    
                        if found_game_log["two_pt_conv"] != int(get_nested(player, ["Passing", "passingTwoPointConversion"])) + int(get_nested(player, ["Rushing", "rushingTwoPointConversion"])) + int(get_nested(player, ["Receiving", "receivingTwoPointConversion"])):
                            update = 1
                        if found_game_log["yahoo_pts"] != round(float(player["fantasyPoints"]), 2):
                            update = 1  

                        if update == 1:
                            nfl_game_logs.update_one(
                                {"_id": ObjectId(found_game_log["_id"])},
                                {"$set": {
                                    "pass_yds": int(get_nested(player, ["Passing", "passYds"])),
                                    "pass_tds": int(get_nested(player, ["Passing", "passTD"])),
                                    "ints": int(get_nested(player, ["Passing", "int"])),
                                    "rush_yds": int(get_nested(player, ["Rushing", "rushYds"])),
                                    "receptions": int(get_nested(player, ["Receiving", "receptions"])),
                                    "rec_yds": int(get_nested(player, ["Receiving", "recYds"])),
                                    "fumbles": int(get_nested(player, ["Defense", "fumblesLost"])),
                                    "tds": int(get_nested(player, ["Rushing", "rushTD"])) + int(get_nested(player, ["Receiving", "recTD"])) + int(get_nested(player, ["Kicking", "kickReturnTD"])) + int(get_nested(player, ["Punting", "puntReturnTD"])),
                                    "two_pt_conv": int(get_nested(player, ["Passing", "passingTwoPointConversion"])) + int(get_nested(player, ["Rushing", "rushingTwoPointConversion"])) + int(get_nested(player, ["Receiving", "receivingTwoPointConversion"])),
                                    "yahoo_pts": round(float(player["fantasyPoints"]), 2)
                                }}
                            )       
                            print(f"updated {player['playerID']} {player['longName']}")
                            updated_players.append(player["playerID"])
                        else:
                            print(f"no change for {player['playerID']} {player['longName']}")
                                
                    else:
                        if "Passing" in player.keys() or "Rushing" in player.keys() or "Receiving" in player.keys():
                            game_log = {}
                            game_log["player_id"] = int(player["playerID"])
                            game_log["player_name"] = player["longName"]
                            game_log["team_id"] = int(player["teamID"])
                            game_log["team_abbv"] = player["teamAbv"]
                            game_log["season"] = current_season
                            game_log["week"] = current_week
                            if player["teamAbv"] == box["home"]:
                                game_log["opponent"] = box["away"]
                            else:
                                game_log["opponent"] = box["home"]
                            game_log["pass_yds"] = int(get_nested(player, ["Passing", "passYds"]))
                            game_log["pass_tds"] = int(get_nested(player, ["Passing", "passTD"]))
                            game_log["ints"] = int(get_nested(player, ["Passing", "int"]))
                            game_log["rush_yds"] = int(get_nested(player, ["Rushing", "rushYds"]))
                            game_log["receptions"] = int(get_nested(player, ["Receiving", "receptions"]))
                            game_log["rec_yds"] = int(get_nested(player, ["Receiving", "recYds"]))
                            game_log["fumbles"] = int(get_nested(player, ["Defense", "fumblesLost"]))
                            game_log["tds"] = int(get_nested(player, ["Rushing", "rushTD"])) + int(get_nested(player, ["Receiving", "recTD"])) + int(get_nested(player, ["Kicking", "kickReturnTD"])) + int(get_nested(player, ["Punting", "puntReturnTD"]))
                            game_log["two_pt_conv"] = int(get_nested(player, ["Passing", "passingTwoPointConversion"])) + int(get_nested(player, ["Rushing", "rushingTwoPointConversion"])) + int(get_nested(player, ["Receiving", "receivingTwoPointConversion"]))
                            game_log["def_pts_allowed"] = 0
                            game_log["def_sacks"] = 0
                            game_log["def_fumble_rec"] = 0
                            game_log["def_ints"] = 0
                            game_log["def_blk_kicks"] = 0
                            game_log["def_safeties"] = 0
                            game_log["def_tds_scored"] = 0
                            game_log["yahoo_pts"] = round(float(player["fantasyPoints"]), 2)
                            
                            game_log_inserts.append(game_log)
                            
                            print(f"inserted new game log for {player['playerID']} {player['longName']}")
                            updated_players.append(int(player["playerID"]))

            for d in box["DST"]:
                dst = box["DST"][d]
                if game_log_exists := nfl_game_logs.find_one({
                        "player_id": int(dst["teamID"]),
                        "season": current_season,
                        "week": current_week
                    }) is not None:
                    found_game_log = nfl_game_logs.find_one({
                        "player_id": int(dst["teamID"]),
                        "season": current_season,
                        "week": current_week
                    })
                    update = 0
                    if found_game_log["def_pts_allowed"] != int(dst["ptsAllowed"]):
                        update = 1
                    if found_game_log["def_sacks"] != int(dst["sacks"]):
                        update = 1
                    if found_game_log["def_fumble_rec"] != int(dst["fumblesRecovered"]):
                        update = 1    
                    if found_game_log["def_ints"] != int(dst["defensiveInterceptions"]):
                        update = 1      
                    if found_game_log["def_safeties"] != int(dst["safeties"]):
                        update = 1    
                    if found_game_log["def_tds_scored"] != int(dst["defTD"]):
                        update = 1   

                    if update == 1:
                        nfl_game_logs.update_one(
                            {"_id": ObjectId(found_game_log["_id"])},
                            {"$set": {
                                "def_pts_allowed": int(dst["ptsAllowed"]),
                                "def_sacks": int(dst["sacks"]),
                                "def_fumble_rec": int(dst["fumblesRecovered"]),
                                "def_ints": int(dst["defensiveInterceptions"]),
                                "def_safeties": int(dst["safeties"]),
                                "def_tds_scored": int(dst["defTD"]),
                            }}
                        )       
                        print(f"updated {dst['teamAbv']}")
                        updated_players.append(int(dst["teamID"]))
                    else:
                        print(f"no change for {dst['teamAbv']} Defense")
                            
                else:
                    game_log = {}
                    game_log["player_id"] = int(dst["teamID"])
                    game_log["player_name"] = dst["teamAbv"] + " Defense"
                    game_log["team_id"] = int(dst["teamID"])
                    game_log["team_abbv"] = dst["teamAbv"]
                    game_log["season"] = current_season
                    game_log["week"] = current_week
                    game_log["pass_yds"] = 0
                    game_log["pass_tds"] = 0
                    game_log["ints"] = 0
                    game_log["rush_yds"] = 0
                    game_log["receptions"] = 0
                    game_log["rec_yds"] = 0
                    game_log["fumbles"] = 0
                    game_log["tds"] = 0
                    game_log["two_pt_conv"] = 0
                    game_log["def_pts_allowed"] = int(dst["ptsAllowed"])
                    game_log["def_sacks"] = int(dst["sacks"])
                    game_log["def_fumble_rec"] = int(dst["fumblesRecovered"])
                    game_log["def_ints"] = int(dst["defensiveInterceptions"])
                    game_log["def_blk_kicks"] = 0
                    game_log["def_safeties"] = 0
                    game_log["def_tds_scored"] = int(dst["defTD"])
                    game_log["yahoo_pts"] = 0
                    
                    game_log_inserts.append(game_log)
                    
                    print(f"inserted new game log for {dst['teamAbv']}")
                    updated_players.append(int(dst['teamID']))

    if len(game_log_inserts) > 0:
        nfl_game_logs.insert_many(game_log_inserts)

    data = {
        "players": updated_players,
        "teams": locked_teams
    }
    return data

def update_lineups(updated_players, locked_teams):
    found_team_lineups = lineups.find({"week": current_week, "season": current_season})

    for lineup in found_team_lineups:
        for idx, selection in enumerate(lineup["selections"]):
            if "team_id" in selection.keys() and selection["team_id"] in locked_teams:
                lineups.update_one(
                    {"_id": ObjectId(lineup["_id"])},
                    {
                        "$set": { 
                            f"selections.{idx}.locked": True
                        }
                    }
                )   

    # iterate through list of player IDs
    for player in updated_players:
        print(f"checking lineups for player {player} {current_season} {current_week}")
        try:
            game_log = nfl_game_logs.find_one({"player_id": int(player), "week": int(current_week), "season": int(current_season)})
        # find lineups with that player Id and matches current week
            found_player_lineups = lineups.find({"selections.player_id": int(player), "week": int(current_week), "season": int(current_season)}) 

            for lineup in found_player_lineups:
                print(f"found selection for {player} in lineup {lineup['_id']}")
                league = leagues.find_one({"_id": ObjectId(lineup["league_id"])})
                scoring = league["scoring"]["statistics"]
                game_log_fantasy_stats = {}
                for k, v in scoring.items():
                    if k == "def_pts_allowed" and game_log["player_id"] == game_log["team_id"]:
                        if game_log[k] == 0:
                            game_log_fantasy_stats[k] = 10
                        elif game_log[k] > 0 and game_log[k] < 7:
                            game_log_fantasy_stats[k] = 7
                        elif game_log[k] >= 7 and game_log[k] < 14:
                            game_log_fantasy_stats[k] = 4
                        elif game_log[k] >= 14 and game_log[k] < 21:
                            game_log_fantasy_stats[k] = 1
                        elif game_log[k] >= 21 and game_log[k] < 28:
                            game_log_fantasy_stats[k] = 0
                        elif game_log[k] >= 28 and game_log[k] < 35:
                            game_log_fantasy_stats[k] = -1
                        else:
                            game_log_fantasy_stats[k] = -4
                    else:
                        game_log_fantasy_stats[k] = round(game_log[k] * v, 2)
                    # defensive points allowed
                fantasy_stats_dict = { k:v for (k,v) in game_log_fantasy_stats.items()}
                total_points = sum(round(value, 2) for value in game_log_fantasy_stats.values())
                selection_index = next((i for i, item in enumerate(lineup["selections"]) if item["player_id"] == int(player)))
                lineup_score = 0
                for selection in lineup["selections"]:
                    # if "player_id" in selection.keys():
                    #     if selection["player_id"] == player:
                    #         selection_index = selection["index"]
                    #     if selection["player_id"] != player and "total_points" in selection.keys():
                    #         lineup_score += selection["total_points"]
                    if selection["index"] != selection_index and "total_points" in selection.keys():
                        lineup_score += selection["total_points"]
                        
                lineup_score += total_points

                if "fantasy_stats" not in lineup["selections"][selection_index].keys():
                    print("inserting first fantasy stats for player in lineup")

                    lineups.update_one(
                        {"_id": ObjectId(lineup["_id"])},
                        {
                            "$set": { 
                                f"selections.{selection_index}.locked": True,
                                f"selections.{selection_index}.fantasy_stats": fantasy_stats_dict,
                                f"selections.{selection_index}.total_points": total_points,
                                f"score": lineup_score
                            }
                        }
                    )   
                else:
                    print("updating fantasy stats for player in lineup")
                    lineups.update_one(
                        {"_id": ObjectId(lineup["_id"])},
                        {
                            "$set": { 
                                f"selections.{selection_index}.fantasy_stats": fantasy_stats_dict,
                                f"selections.{selection_index}.total_points": total_points,
                                f"score": lineup_score
                            }
                        }
                    )  

                found_matchup = matchups.find_one({"team_1_id": ObjectId(lineup["contestant_id"]), "season": current_season, "week": current_week})  

                if found_matchup:
                    matchups.update_one(
                        {"_id": ObjectId(found_matchup["_id"])},
                        {
                            "$set": { 
                                f"team_1_score": lineup_score
                            }
                        }
                    )  
                else:
                    found_matchup_two = matchups.find_one({"team_2_id": ObjectId(lineup["contestant_id"]), "season": current_season, "week": current_week}) 
                    matchups.update_one(
                        {"_id": ObjectId(found_matchup_two["_id"])},
                        {
                            "$set": { 
                                f"team_2_score": lineup_score
                            }
                        }
                    )   
        except Exception as e: print(e)

    return

get_games()
data = get_player_game_logs()
update_lineups(data["players"], data["teams"])

