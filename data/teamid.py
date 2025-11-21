import os
import json
import re

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# Update these paths to match your actual folder structure
TEAM_DATA_DIR = "./mlb_team_data"
PLAYER_DATA_DIR = "./mlb_player_data_rev"

# ---------------------------------------------------------
# STEP 1: BUILD TEAM MAPPING
# ---------------------------------------------------------
def build_team_map(team_dir):
    """
    Scans the team directory to create a dictionary:
    {'Arizona Diamondbacks': 109, 'New York Yankees': 147, ...}
    """
    print(f"--- Building Team Map from {team_dir} ---")
    team_map = {}
    
    # Regex to parse filenames like: "109_Arizona Diamondbacks.json"
    # Group 1: digits (ID), Group 2: text (Name)
    filename_pattern = re.compile(r"(\d+)_(.+)\.json")

    if not os.path.exists(team_dir):
        print(f"ERROR: Team directory '{team_dir}' not found.")
        return {}

    for root, dirs, files in os.walk(team_dir):
        for filename in files:
            if filename.endswith(".json"):
                match = filename_pattern.match(filename)
                if match:
                    team_id = int(match.group(1))
                    team_name = match.group(2).strip()
                    
                    # Store in map
                    team_map[team_name] = team_id
                    # Also handle lowercase just in case
                    team_map[team_name.lower()] = team_id
    
    print(f"Found {len(team_map)} unique team mappings.")
    return team_map

# ---------------------------------------------------------
# STEP 2: UPDATE PLAYER FILES
# ---------------------------------------------------------
def update_player_files(player_dir, team_map):
    print(f"\n--- Updating Player Files in {player_dir} ---")
    
    count_updated = 0
    count_skipped = 0
    count_unknown_team = 0

    if not os.path.exists(player_dir):
        print(f"ERROR: Player directory '{player_dir}' not found.")
        return

    for root, dirs, files in os.walk(player_dir):
        # The 'root' variable is the current folder path.
        # Example: ./mlb_player_data/2021/Arizona Diamondbacks
        
        # Get the folder name (which should be the Team Name)
        current_folder_name = os.path.basename(root)
        
        # Check if this folder name exists in our map
        # We try exact match, then lower case match
        team_id = team_map.get(current_folder_name) or team_map.get(current_folder_name.lower())

        if not team_id:
            # If we are in the root '2021' folder, it won't match a team name, so just skip silently
            continue

        for filename in files:
            if filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                
                try:
                    # 1. Read the file
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 2. Check if we need to update
                    # We update if 'team_id' is missing OR different
                    existing_id = data.get('team_id')
                    
                    if existing_id != team_id:
                        # 3. Modify Data
                        data['team_id'] = team_id
                        data['team_name'] = current_folder_name
                        
                        # 4. Write back to file
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        
                        print(f"Updated: {filename} -> Team: {current_folder_name} ({team_id})")
                        count_updated += 1
                    else:
                        count_skipped += 1
                        
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    print("-" * 40)
    print(f"Summary:")
    print(f"Files Updated: {count_updated}")
    print(f"Files Already Correct: {count_skipped}")

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1. Build the dictionary of Team Name -> Team ID
    mapping = build_team_map(TEAM_DATA_DIR)
    
    if mapping:
        # 2. Apply it to the player files
        update_player_files(PLAYER_DATA_DIR, mapping)
    else:
        print("Could not build team mapping. Please check your mlb_team_data folder.")