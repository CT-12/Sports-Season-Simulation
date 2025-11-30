import psycopg2
import pprint
import json
# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
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

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_verification():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=== DATABASE VERIFICATION REPORT ===\n")

    # 1. Check Table Counts
    tables = [
        "Teams", 
        "Players", 
        "Player_Hitting_Stats", 
        "Player_Pitching_Stats", 
        "Team_Hitting_Stats", 
        "Team_Pitching_Stats"
    ]
    
    print("--- Row Counts ---")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"{table.ljust(25)} : {count}")

    # 2. Verify Specific Player (Shohei Ohtani - ID 660271)
    print("\n--- Sample Player Verification (Shohei Ohtani) ---")
    player_id = 660271
    
    # Fetch Basic Info
    cursor.execute("""
        SELECT player_name, season, position_name 
        FROM Players WHERE player_id = %s
    """, (player_id,))
    player = cursor.fetchone()
    
    if player:
        print(f"Player Found: {player}")
        
        # Fetch Hitting Stats
        cursor.execute("""
            SELECT hr, rbi, avg, ops 
            FROM Player_Hitting_Stats WHERE player_id = %s
        """, (player_id,))
        hitting = cursor.fetchone()
        print(f"Hitting Stats (HR, RBI, AVG, OPS): {hitting}")
        
        # Fetch Pitching Stats
        cursor.execute("""
            SELECT w, l, era, ip, so 
            FROM Player_Pitching_Stats WHERE player_id = %s
        """, (player_id,))
        pitching = cursor.fetchone()
        print(f"Pitching Stats (W, L, ERA, IP, SO): {pitching}")
    else:
        print("Player 660271 not found!")

    # 3. Verify Specific Team (Dodgers - ID 119)
    print("\n--- Sample Team Verification (Los Angeles Dodgers) ---")
    team_id = 119
    
    cursor.execute("SELECT team_name, season FROM Teams WHERE team_id = %s", (team_id,))
    team = cursor.fetchone()
    
    if team:
        print(f"Team Found: {team}")
        
        cursor.execute("SELECT w, l, era FROM Team_Pitching_Stats WHERE team_id = %s", (team_id,))
        t_pitch = cursor.fetchone()
        print(f"Team Pitching (W, L, ERA): {t_pitch}")
    else:
        print("Team 119 not found!")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_verification()