from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

client = MongoClient(os.environ["MONGODB_URI"])

current_week = 1
current_season = 2024

db = client.ff_db
player_season_stats = db["PlayerSeasonStats"]

def season_stats(player_ids):
    new_season_stats = []
    for updated_player_id in player_ids:
        result = list(db['NFLGameLogs'].aggregate([
            {
                '$match': {
                    'player_id': updated_player_id,
                    'season': current_season
                }
            }, {
                '$group': {
                    '_id': '$player_id', 
                    'total_games': {'$sum': 1},
                    'total_pass_yds': { '$sum': '$pass_yds' },
                    'total_pass_tds': { '$sum': '$pass_tds' },
                    'total_ints': { '$sum': '$ints' },
                    'total_rush_yds': { '$sum': '$rush_yds' },
                    'total_receptions': { '$sum': '$receptions' },
                    'total_rec_yds': { '$sum': '$rec_yds' },
                    'total_fumbles': { '$sum': '$fumbles' },
                    'total_tds': { '$sum': '$tds' },
                    'total_two_pt_conv': { '$sum': '$two_pt_conv' },
                    'total_def_pts_allowed': { '$sum': '$def_pts_allowed' },
                    'total_def_sacks': { '$sum': '$def_sacks' },
                    'total_def_fumble_rec': { '$sum': '$def_fumble_rec' },
                    'total_def_ints': { '$sum': '$def_ints' },
                    'total_def_blk_kicks': { '$sum': '$def_blk_kicks' },
                    'total_def_safeties': { '$sum': '$def_safeties' },
                    'total_def_tds_scored': { '$sum': '$def_tds_scored' },
                    'total_yahoo_pts': { '$sum': '$yahoo_pts' }
                }
            }
        ]))

        if len(result) > 0:
            result_obj = result[0]
        else:
            continue

        if season_stat_exists := player_season_stats.find_one({
            "player_id": updated_player_id,
            "season": current_season
            }) is not None:
                found_season_stat = player_season_stats.find_one({
                "player_id": updated_player_id,
                "season": current_season
                })
                player_season_stats.update_one(
                    {"_id": ObjectId(found_season_stat["_id"])},
                    {"$set": {
                        "stats.games": result_obj["total_games"],
                        "stats.pass_yds": result_obj["total_pass_yds"],
                        "stats.pass_tds": result_obj["total_pass_tds"],
                        "stats.ints": result_obj["total_ints"],
                        "stats.rush_yds": result_obj["total_rush_yds"],
                        "stats.receptions": result_obj["total_receptions"],
                        "stats.rec_yds": result_obj["total_rec_yds"],
                        "stats.fumbles": result_obj["total_fumbles"],
                        "stats.tds": result_obj["total_tds"],
                        "stats.two_pt_conv": result_obj["total_two_pt_conv"],
                        "stats.def_pts_allowed": result_obj["total_def_pts_allowed"],
                        "stats.def_sacks": result_obj["total_def_sacks"],
                        "stats.def_fumble_rec": result_obj["total_def_fumble_rec"],
                        "stats.def_ints": result_obj["total_def_ints"],
                        "stats.def_blk_kicks": result_obj["total_def_blk_kicks"],
                        "stats.def_safeties": result_obj["total_def_safeties"],
                        "stats.def_tds_scored": result_obj["total_def_tds_scored"],
                        "stats.yahoo_pts": result_obj["total_yahoo_pts"]
                    }}
                )       
                print(f"updated season stats for player {updated_player_id}")           
        else:
            season_stats = {}
            season_stats["player_id"] = updated_player_id
            season_stats["sport"] = "NFL"
            season_stats["season"] = current_season
            season_stats["stats"] = {}
            season_stats["stats"]["games"] = result_obj["total_games"]
            season_stats["stats"]["pass_yds"] = result_obj["total_pass_yds"]
            season_stats["stats"]["pass_tds"] = result_obj["total_pass_tds"]
            season_stats["stats"]["ints"] = result_obj["total_ints"]
            season_stats["stats"]["rush_yds"] = result_obj["total_rush_yds"]
            season_stats["stats"]["receptions"] = result_obj["total_receptions"]
            season_stats["stats"]["rec_yds"] = result_obj["total_rec_yds"]
            season_stats["stats"]["fumbles"] = result_obj["total_fumbles"]
            season_stats["stats"]["tds"] = result_obj["total_tds"]
            season_stats["stats"]["two_pt_conv"] = result_obj["total_two_pt_conv"]
            season_stats["stats"]["def_pts_allowed"] = result_obj["total_def_pts_allowed"]
            season_stats["stats"]["def_sacks"] = result_obj["total_def_sacks"]
            season_stats["stats"]["def_fumble_rec"] = result_obj["total_def_fumble_rec"]        
            season_stats["stats"]["def_ints"] = result_obj["total_def_ints"]        
            season_stats["stats"]["def_blk_kicks"] = result_obj["total_def_blk_kicks"]        
            season_stats["stats"]["def_safeties"] = result_obj["total_def_safeties"]        
            season_stats["stats"]["def_tds_scored"] = result_obj["total_def_tds_scored"]              
            season_stats["stats"]["yahoo_pts"] = result_obj["total_yahoo_pts"]              
            new_season_stats.append(season_stats)
            print(f"Inserting new season stats for player {updated_player_id}")
    
    if len(new_season_stats) > 0:
        player_season_stats.insert_many(new_season_stats)