import json
import os
import psycopg2
import sys

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
def load_db_config(config_file="config.json"):
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: '{config_file}' not found. Please create it.")
        sys.exit(1)

DB_CONFIG = load_db_config()

# ---------------------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------------------
def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

# ---------------------------------------------------------
# CORE LOGIC: THE FIX
# ---------------------------------------------------------
def fix_player_team_id(cursor, data):
    """
    Performs an UPSERT (Insert or Update) to ensure the player exists
    and has the correct current_team_id.
    """
    player_id = data.get('player_id')
    season = data.get('season')
    player_name = data.get('player_name', 'Unknown')
    
    # 1. Extract the Team ID (This is the critical missing piece)
    current_team_id = data.get('team_id')

    # 2. Extract Position Info (Needed if we have to INSERT a new row)
    pos = data.get('position_info', {})
    p_code = pos.get('position_code')
    p_name = pos.get('position_name')
    p_type = pos.get('position_type')

    if not player_id or not season:
        return False # Skip invalid data

    # 3. The "NEW SQL" Strategy: ON CONFLICT DO UPDATE
    # This acts as a "Smart Fix":
    # - If the player isn't there, add them.
    # - If they ARE there, just update the team_id.
    sql = """
        INSERT INTO Players 
        (player_id, season, player_name, current_team_id, position_code, position_name, position_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_id, season) 
        DO UPDATE SET 
            current_team_id = EXCLUDED.current_team_id;
    """

    cursor.execute(sql, (
        player_id, 
        season, 
        player_name, 
        current_team_id, 
        p_code, 
        p_name, 
        p_type
    ))
    return True

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    count_updated = 0
    count_skipped = 0

    # 1. Get folder path
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]
    else:
        target_folder = input("Enter the path to the JSON data folder: ").strip()

    if not target_folder or not os.path.exists(target_folder):
        print("Error: Invalid folder path.")
        return

    print(f"--- Starting Fix Process in: {target_folder} ---")

    # 2. Walk through files
    for root, dirs, files in os.walk(target_folder):
        for filename in files:
            if filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                        # Only process files that are PLAYERS (have player_id)
                        if 'player_id' in data:
                            success = fix_player_team_id(cursor, data)
                            if success:
                                count_updated += 1
                                # Optional: Print progress every 1000 records
                                if count_updated % 1000 == 0:
                                    print(f"Processed {count_updated} players...")
                                    conn.commit() 
                        else:
                            count_skipped += 1

                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    # 3. Final Commit
    conn.commit()
    cursor.close()
    conn.close()

    print("------------------------------------------------")
    print(f"FIX COMPLETE.")
    print(f"Total Players Processed/Fixed: {count_updated}")
    print(f"Non-player files skipped: {count_skipped}")

if __name__ == "__main__":
    main()