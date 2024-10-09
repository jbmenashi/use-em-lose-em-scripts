from pymongo import MongoClient
from bson import ObjectId
import requests
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])
db = client.ff_db
player_projections = db["PlayerProjections"]

projection_season = 2024
projection_week = 6

def get_player_projections():
    schedule_url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLGamesForWeek"

    schedule_querystring = {"week":f"{projection_week}","seasonType":"reg","season":f"{projection_season}"}

    schedule_headers = {
        "x-rapidapi-key": os.environ["RAPID_API_KEY"],
        "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    schedule_res = requests.get(schedule_url, headers=schedule_headers, params=schedule_querystring)
    games = {}
    for game in schedule_res.json()["body"]:
        print("home", game['teamIDHome'])
        games[f"{game['teamIDHome']}"] = {}
        games[f"{game['teamIDHome']}"]["location"] = "Home"
        games[f"{game['teamIDHome']}"]["opponent"] = game["away"]
        games[f"{game['teamIDHome']}"]["opponent_id"] = game['teamIDAway']
        games[f"{game['teamIDHome']}"]["game_time"] = game["gameTime"]
        print("away", game['teamIDAway'])
        games[f"{game['teamIDAway']}"] = {}
        games[f"{game['teamIDAway']}"]["location"] = "Away"
        games[f"{game['teamIDAway']}"]["opponent"] = game["home"]
        games[f"{game['teamIDAway']}"]["opponent_id"] = game['teamIDHome']
        games[f"{game['teamIDAway']}"]["game_time"] = game["gameTime"]

    projection_inserts = []

    url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLProjections"

    querystring = {f"week":{projection_week},"archiveSeason":"2024","twoPointConversions":"2","passYards":".04","passAttempts":"0","passTD":"4","passCompletions":"0","passInterceptions":"-1","pointsPerReception":"0.5","carries":"0","rushYards":".1","rushTD":"6","fumbles":"-2","receivingYards":".1","receivingTD":"6","targets":"0","fgMade":"0","fgMissed":"0","xpMade":"0","xpMissed":"0"}

    headers = {
        "x-rapidapi-key": os.environ["RAPID_API_KEY"],
        "x-rapidapi-host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    res = requests.get(url, headers=headers, params=querystring)

    for p in res.json()["body"]["playerProjections"]:
        player = res.json()["body"]["playerProjections"][p]

        # score = (player["PassingYards"] * 0.04) + (player["PassingTouchdowns"] * 4) + (player["PassingInterceptions"] * -1) + (player["RushingYards"] * 0.1) + (player["Receptions"] * 0.5) + (player["ReceivingYards"] * 0.1) + (player["Fumbles"] * -2) + (player["Touchdowns"] * 6)

        if projection_exists := player_projections.find_one({
                "player_id": int(player["playerID"]),
                "season": projection_season,
                "week": projection_week
            }) is not None:
            found_projection = player_projections.find_one({
                "player_id": int(player["playerID"]),
                "season": projection_season,
                "week": projection_week
            })
            update = 0
            if found_projection["stats"]["pass_yds"] != round(float(player["Passing"]["passYds"]), 2):
                update = 1
            if found_projection["stats"]["pass_tds"] != round(float(player["Passing"]["passTD"]), 2):
                update = 1
            if found_projection["stats"]["ints"] != round(float(player["Passing"]["int"]), 2):
                update = 1    
            if found_projection["stats"]["rush_yds"] != round(float(player["Rushing"]["rushYds"]), 2):
                update = 1     
            if found_projection["stats"]["receptions"] != round(float(player["Receiving"]["receptions"]), 2):
                update = 1    
            if found_projection["stats"]["rec_yds"] != round(float(player["Receiving"]["recYds"]), 2):
                update = 1    
            if found_projection["stats"]["fumbles"] != round(float(player["fumblesLost"]), 2):
                update = 1    
            if found_projection["stats"]["tds"] != round(float(player["Rushing"]["rushTD"]), 2) + round(float(player["Receiving"]["recTD"]), 2):
                update = 1    
            if found_projection["stats"]["two_pt_conv"] != round(float(player["twoPointConversion"]), 2):
                update = 1    
            if found_projection["stats"]["score"] != round(float(player["fantasyPoints"]), 2):
                update = 1    

            if update == 1:
                player_projections.update_one(
                    {"_id": ObjectId(found_projection["_id"])},
                    {"$set": {
                        "stats.pass_yds": round(float(player["Passing"]["passYds"]), 2),
                        "stats.pass_tds": round(float(player["Passing"]["passTD"]), 2),
                        "stats.ints": round(float(player["Passing"]["int"]), 2),
                        "stats.rush_yds": round(float(player["Rushing"]["rushYds"]), 2),
                        "stats.receptions": round(float(player["Receiving"]["receptions"]), 2),
                        "stats.rec_yds": round(float(player["Receiving"]["recYds"]), 2),
                        "stats.fumbles": round(float(player["fumblesLost"]), 2),
                        "stats.tds": round(float(player["Rushing"]["rushTD"]), 2) + round(float(player["Receiving"]["recTD"]), 2),
                        "stats.two_pt_conv": round(float(player["twoPointConversion"]), 2),
                        "stats.score": round(float(player["fantasyPoints"]), 2)
                    }}
                )       
                print(f"updated projection for {player['longName']} for week {projection_week}")
            else:
                print(f"no projection change for {player['longName']} for week {projection_week}")
                    
        else:
            if player["pos"] in ["QB", "RB", "WR", "TE", "FB"] and player["teamID"] in games.keys():
                projection = {}
                projection["player_id"] = int(player["playerID"])
                projection["player_name"] = player["longName"]
                projection["team_id"] = int(player["teamID"])
                projection["team_abbv"] = player["team"]
                projection["sport"] = "NFL"
                projection["season"] = projection_season
                projection["week"] = projection_week
                projection["opponent"] = games[f"{player['teamID']}"]["opponent"]
                projection["opponent_team_id"] = int(games[f"{player['teamID']}"]["opponent_id"])
                projection["location"] = games[f"{player['teamID']}"]["location"]
                projection["game_time"] = games[f"{player['teamID']}"]["game_time"]
                projection["stats"] = {}
                projection["stats"]["pass_yds"] = round(float(player["Passing"]["passYds"]), 2)
                projection["stats"]["pass_tds"] = round(float(player["Passing"]["passTD"]), 2)
                projection["stats"]["ints"] = round(float(player["Passing"]["int"]), 2)
                projection["stats"]["rush_yds"] = round(float(player["Rushing"]["rushYds"]), 2)
                projection["stats"]["receptions"] = round(float(player["Receiving"]["receptions"]), 2)
                projection["stats"]["rec_yds"] = round(float(player["Receiving"]["recYds"]), 2)
                projection["stats"]["fumbles"] = round(float(player["fumblesLost"]), 2)
                projection["stats"]["tds"] = round(float(player["Rushing"]["rushTD"]), 2) + round(float(player["Receiving"]["recTD"]), 2)
                projection["stats"]["two_pt_conv"] = round(float(player["twoPointConversion"]), 2)
                projection["stats"]["def_pts_allowed"] = 0
                projection["stats"]["def_sacks"] = 0
                projection["stats"]["def_fumble_rec"] = 0
                projection["stats"]["def_ints"] = 0
                projection["stats"]["def_blk_kicks"] = 0
                projection["stats"]["def_safeties"] = 0
                projection["stats"]["def_tds_scored"] = 0
                projection["stats"]["score"] = round(float(player["fantasyPoints"]), 2)
                projection_inserts.append(projection)
                
                print(f"inserted new projection for {player['longName']} for week {projection_week}")

    for d in res.json()["body"]["teamDefenseProjections"]:
        dst = res.json()["body"]["teamDefenseProjections"][d]

        # score = (player["Sacks"]) + (player["FumblesRecovered"] * 2) + (player["Interceptions"] * 2) + (player["BlockedKicks"] * 2) + (player["Safeties"] * 3) + (player["TouchdownsScored"] * 6)      

        # if player["PointsAllowed"] == 0:
        #     score += 10
        # elif player["PointsAllowed"] > 0 and player["PointsAllowed"] < 7:
        #     score += 7
        # elif player["PointsAllowed"] >= 7 and player["PointsAllowed"] < 14:
        #     score += 4
        # elif player["PointsAllowed"] >= 14 and player["PointsAllowed"] < 21:
        #     score += 1
        # elif player["PointsAllowed"] >= 21 and player["PointsAllowed"] < 28:
        #     score += 0
        # elif player["PointsAllowed"] >= 28 and player["PointsAllowed"] < 35:
        #     score += -1
        # else:
        #     score += -4

        if projection_exists := player_projections.find_one({
                "player_id": int(dst["teamID"]),
                "season": projection_season,
                "week": projection_week
            }) is not None:
            found_projection = player_projections.find_one({
                "player_id": int(dst["teamID"]),
                "season": projection_season,
                "week": projection_week
            })
            update = 0
            if found_projection["stats"]["def_pts_allowed"] != round(float(dst["ptsAgainst"]), 2):
                update = 1
            if found_projection["stats"]["def_sacks"] != round(float(dst["sacks"]), 2):
                update = 1
            if found_projection["stats"]["def_fumble_rec"] != round(float(dst["fumbleRecoveries"]), 2):
                update = 1    
            if found_projection["stats"]["def_ints"] != round(float(dst["interceptions"]), 2):
                update = 1     
            if found_projection["stats"]["def_blk_kicks"] != round(float(dst["blockKick"]), 2):
                update = 1    
            if found_projection["stats"]["def_safeties"] != round(float(dst["safeties"]), 2):
                update = 1    
            if found_projection["stats"]["def_tds_scored"] != round(float(dst["defTD"]), 2):
                update = 1      
            if found_projection["stats"]["score"] != round(float(dst["fantasyPointsDefault"]), 2):
                update = 1      

            if update == 1:
                player_projections.update_one(
                    {"_id": ObjectId(found_projection["_id"])},
                    {"$set": {
                        "stats.def_pts_allowed": round(float(dst["ptsAgainst"]), 2),
                        "stats.def_sacks": round(float(dst["sacks"]), 2),
                        "stats.def_fumble_rec": round(float(dst["fumbleRecoveries"]), 2),
                        "stats.def_ints": round(float(dst["interceptions"]), 2),
                        "stats.def_blk_kicks": round(float(dst["blockKick"]), 2),
                        "stats.def_safeties": round(float(dst["safeties"]), 2),
                        "stats.def_tds_scored": round(float(dst["defTD"]), 2),
                        "stats.score": round(float(dst["fantasyPointsDefault"]), 2)
                    }}
                )       
                print(f"updated projection for {dst['teamAbv']} Defense for week {projection_week}")
            else:
                print(f"no projection change for {dst['teamAbv']} Defense for week {projection_week}")
                    
        else:
            projection = {}
            projection["player_id"] = int(dst["teamID"])
            projection["player_name"] = dst["teamAbv"] + " Defense"
            projection["team_id"] = int(dst["teamID"])
            projection["team_abbv"] = dst["teamAbv"]
            projection["sport"] = "NFL"
            projection["season"] = projection_season
            projection["week"] = projection_week
            if f"{dst['teamID']}" in games.keys():
                projection["opponent"] = games[f"{dst['teamID']}"]["opponent"]
                projection["opponent_team_id"] = int(games[f"{dst['teamID']}"]["opponent_id"])
                projection["location"] = games[f"{dst['teamID']}"]["location"]
                projection["game_time"] = games[f"{dst['teamID']}"]["game_time"]
            else:
                projection["opponent"] = ""
                projection["opponent_team_id"] = 0
                projection["location"] = ""
                projection["game_time"] = ""          
            projection["stats"] = {}
            projection["stats"]["pass_yds"] = 0
            projection["stats"]["pass_tds"] = 0
            projection["stats"]["ints"] = 0
            projection["stats"]["rush_yds"] = 0
            projection["stats"]["receptions"] = 0
            projection["stats"]["rec_yds"] = 0
            projection["stats"]["fumbles"] = 0
            projection["stats"]["tds"] = 0
            projection["stats"]["two_pt_conv"] = 0
            projection["stats"]["def_pts_allowed"] = round(float(dst["ptsAgainst"]), 2)
            projection["stats"]["def_sacks"] = round(float(dst["sacks"]), 2)
            projection["stats"]["def_fumble_rec"] = round(float(dst["fumbleRecoveries"]), 2)
            projection["stats"]["def_ints"] = round(float(dst["interceptions"]), 2)
            projection["stats"]["def_blk_kicks"] = round(float(dst["blockKick"]), 2)
            projection["stats"]["def_safeties"] = round(float(dst["safeties"]), 2)
            projection["stats"]["def_tds_scored"] = round(float(dst["defTD"]), 2)
            projection["stats"]["score"] = round(float(dst["fantasyPointsDefault"]), 2)
            projection_inserts.append(projection)
            
            print(f"inserted new projection for {dst['teamAbv']} Defense for week {projection_week}")

    if len(projection_inserts) > 0:
        player_projections.insert_many(projection_inserts)

    return

get_player_projections()