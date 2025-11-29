import json
import os
import psycopg2
from decimal import Decimal

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
def load_db_config(config_file="config.json"):
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: '{config_file}' not found. Please create it.")
        exit(1)

DB_CONFIG = load_db_config()

JSON_FOLDER = "./"  # Folder where your .json files are located

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def clean_val(value):
    """
    Cleans JSON values for SQL insertion.
    Converts "---", "-", or strings to appropriate types.
    """
    if value is None:
        return None
    if isinstance(value, str):
        clean = value.strip()
        if clean in [".---", "-", "", "null","-.--"]:
            return None
        # Check if it's a decimal string (e.g., ".282")
        try:
            return Decimal(clean)
        except:
            return clean
    return value

# ---------------------------------------------------------
# TEAM IMPORT LOGIC
# ---------------------------------------------------------
def insert_team(cursor, data):
    print(f"Processing Team: {data.get('team_name')}")
    
    team_id = data['team_id']
    season = data['season']
    
    # 1. Insert into Teams
    sql_team = """
        INSERT INTO Teams (team_id, season, team_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (team_id, season) DO NOTHING;
    """
    cursor.execute(sql_team, (team_id, season, data['team_name']))
    
    stats = data.get('stats', {})

    # 2. Insert Hitting Stats
    if 'hitting' in stats:
        h = stats['hitting']
        sql_hit = """
            INSERT INTO Team_Hitting_Stats 
            (team_id, season, ab, r, h, hr, rbi, avg, obp, slg, ops)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(sql_hit, (
            team_id, season,
            clean_val(h.get('atBats')),
            clean_val(h.get('runs')),
            clean_val(h.get('hits')),
            clean_val(h.get('homeRuns')),
            clean_val(h.get('rbi')),
            clean_val(h.get('avg')),
            clean_val(h.get('obp')),
            clean_val(h.get('slg')),
            clean_val(h.get('ops'))
        ))

    # 3. Insert Pitching Stats
    if 'pitching' in stats:
        p = stats['pitching']
        sql_pitch = """
            INSERT INTO Team_Pitching_Stats 
            (team_id, season, w, l, era, ip, h, r, er, bb, so, whip, avg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(sql_pitch, (
            team_id, season,
            clean_val(p.get('wins')),
            clean_val(p.get('losses')),
            clean_val(p.get('era')),
            clean_val(p.get('inningsPitched')),
            clean_val(p.get('hits')),
            clean_val(p.get('runs')),
            clean_val(p.get('earnedRuns')),
            clean_val(p.get('baseOnBalls')),
            clean_val(p.get('strikeOuts')),
            clean_val(p.get('whip')),
            clean_val(p.get('avg'))
        ))
    # --- NEW CODE STARTS HERE ---

    # 4. Insert Game Logs (detailed_games)
    games = data.get('detailed_games', [])
    if games:
        sql_games = """
            INSERT INTO Team_Game_Logs
            (team_id, season, game_id, game_date, game_type, opponent_id, opponent_name, 
             home_away, team_score, opponent_score, result, score_diff)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (team_id, game_id) DO NOTHING;
        """
        
        for g in games:
            cursor.execute(sql_games, (
                team_id, 
                season,
                g.get('game_id'),
                g.get('date'),
                g.get('game_type'),
                g.get('opponent_id'),
                g.get('opponent'), # JSON key is 'opponent', DB col is opponent_name
                g.get('home_away'),
                g.get('team_score'),
                g.get('opponent_score'),
                g.get('result'),
                g.get('score_diff')
            ))

    # 5. Insert VS Records (vs_records)
    vs_recs = data.get('vs_records', [])
    if vs_recs:
        sql_vs = """
            INSERT INTO Team_VS_Records
            (team_id, season, opponent_id, opponent_name, game_type, wins, losses)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (team_id, season, opponent_id, game_type) DO NOTHING;
        """
        
        for v in vs_recs:
            cursor.execute(sql_vs, (
                team_id,
                season,
                v.get('opponent_id'),
                v.get('opponent_name'),
                v.get('game_type'),
                v.get('wins'),
                v.get('losses')
            ))

# ---------------------------------------------------------
# PLAYER IMPORT LOGIC
# ---------------------------------------------------------
 
def insert_player(cursor, data):
    player_name = data.get('player_name', 'Unknown')
    print(f"Processing Player: {player_name}")
    
    player_id = data['player_id']
    season = data['season']
    
    # --- UPDATE: Get Team ID ---
    # This reads the field we added using enrich_players.py
    current_team_id = data.get('team_id') 
    # ---------------------------

    # 1. Get Position Details
    pos = data.get('position_info', {})
    # Convert to string to be safe (e.g., "1" vs 1)
    pos_code = str(pos.get('position_code', '')) 
    
    # "1" is the universal standard for Pitcher
    is_pitcher = (pos_code == '1')
    is_twoway=(pos_code == 'Y')

    # 2. Insert into Players (Main Table)
    sql_player = """
        INSERT INTO Players 
        (player_id, season, player_name, current_team_id, position_code, position_name, position_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_id, season) DO NOTHING;
    """
    
    cursor.execute(sql_player, (
        player_id, season, player_name, current_team_id,
        pos.get('position_code'), pos.get('position_name'), pos.get('position_type'),current_team_id
    ))
    

    stats = data.get('stats', {})

    # ---------------------------------------------------------
    # 3. Insert Hitting Stats Logic
    # ---------------------------------------------------------
    if 'hitting' in stats:
        h = stats['hitting']
        
        # LOGIC: 
        # If they are NOT a pitcher, we expect hitting stats.
        # If they ARE a pitcher, we only insert if they actually had At Bats (AB > 0).
        at_bats = int(h.get('atBats', 0) or 0) # Handle None or "0" safely
        
        should_insert_hitting = (not is_pitcher)  

        if should_insert_hitting:
            sql_hit = """
                INSERT INTO Player_Hitting_Stats 
                (player_id, season, ab, r, h, hr, rbi, avg, obp, slg, ops)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            try:
                cursor.execute(sql_hit, (
                    player_id, season,
                    clean_val(h.get('atBats')),
                    clean_val(h.get('runs')),
                    clean_val(h.get('hits')),
                    clean_val(h.get('homeRuns')),
                    clean_val(h.get('rbi')),
                    clean_val(h.get('avg')),
                    clean_val(h.get('obp')),
                    clean_val(h.get('slg')),
                    clean_val(h.get('ops'))
                ))
            except Exception as err:
                print(f"--- FAILED INSERT DATA FOR {player_name} ---")
                # Print the raw stats to see what looked wrong
                print(json.dumps(h, indent=2)) 
                raise err # Re-raise to trigger the main loop's error handler
                

    # ---------------------------------------------------------
    # 4. Insert Pitching Stats Logic
    # ---------------------------------------------------------
    if 'pitching' in stats:
        p = stats['pitching']
        
        # LOGIC:
        # If they ARE a pitcher, we insert.
        # If they are NOT a pitcher, only insert if they actually pitched (IP > 0).
        ip_val = p.get('inningsPitched', '0')
        if ip_val is None: ip_val = '0'
       

        should_insert_pitching = is_pitcher or is_twoway

        if should_insert_pitching:
            sql_pitch = """
                INSERT INTO Player_Pitching_Stats 
                (player_id, season, w, l, era, ip, h, r, er, bb, so, whip, avg)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            cursor.execute(sql_pitch, (
                player_id, season,
                clean_val(p.get('wins')),
                clean_val(p.get('losses')),
                clean_val(p.get('era')),
                clean_val(p.get('inningsPitched')),
                clean_val(p.get('hits')),
                clean_val(p.get('runs')),
                clean_val(p.get('earnedRuns')),
                clean_val(p.get('baseOnBalls')),
                clean_val(p.get('strikeOuts')),
                clean_val(p.get('whip')),
                clean_val(p.get('avg'))
            ))
    
    


# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
import sys # <--- Add this at the top of your file
import time
def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    count_success = 0
    count_skipped = 0
    # --- CONFIGURATION ---------------------
    BATCH_SIZE = 100      # Commit to DB every 100 files (Prevents memory overflow)
    # SLEEP_TIME = 0.05     # Pause 0.05 seconds per file (Slows down CPU usage)
    # ---------------------------------------
    try:
        # ---------------------------------------------------------
        # 1. Get directory from Command Line or User Input
        # ---------------------------------------------------------
        if len(sys.argv) > 1:
            # If run as: python database.py /path/to/data
            target_folder = sys.argv[1]
        else:
            # If run as: python database.py
            # It will pause and ask you to type the path
            target_folder = input("Enter the path to the JSON data folder: ").strip()
        
        # Default to current directory if user just hits Enter
        if not target_folder:
            print(f"Error: no target folder.")
            return

        # Check if it actually exists before continuing
        if not os.path.exists(target_folder):
            print(f"Error: The folder '{target_folder}' does not exist.")
            return
        # ---------------------------------------------------------

        print(f"Scanning for files in: {os.path.abspath(target_folder)}")

        # 2. Use the new 'target_folder' variable here
        for root, dirs, files in os.walk(target_folder):
            for filename in files:
                if filename.endswith(".json"):
                    filepath = os.path.join(root, filename)
                    
                    print(f"Processing: {filepath}")

                    with open(filepath, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            
                            
                            if 'player_id' in data:
                                insert_player(cursor, data)
                                count_success += 1
                            elif 'team_id' in data:
                                insert_team(cursor, data)
                                count_success += 1
                            else:
                                print(f"   -> SKIPPING: File structure unknown")
                                count_skipped += 1
                                
                        except json.JSONDecodeError:
                            print(f"   -> ERROR: Bad JSON format in {filename}")
                        except Exception as e:
                            print(f"   -> ERROR importing {filename}: {e}")
                    # --- STRATEGY 1: BATCH COMMIT ---
                    # # Every BATCH_SIZE (e.g., 100) records, save to DB to free up memory
                    # if count_success > 0 and count_success % BATCH_SIZE == 0:
                    #     conn.commit()
                    #     print(f"--- Committed batch of {BATCH_SIZE} records (Total: {count_success}) ---")

                    # # --- STRATEGY 2: SLEEP/THROTTLE ---
                    # # Pause briefly to let the CPU/DB breathe
                    # if SLEEP_TIME > 0:
                    #     time.sleep(SLEEP_TIME)
        conn.commit()
        print("------------------------------------------------")
        print(f"Done! Successfully imported {count_success} records.")
        print(f"Skipped {count_skipped} files.")
        
    except Exception as e:
        conn.rollback()
        print(f"Fatal DB Connection Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()