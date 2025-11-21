Here is a comprehensive `README.md` file tailored to the scripts and configuration files provided.

-----

# Baseball Statistics Database Project

This project provides a complete ETL (Extract, Transform, Load) pipeline to ingest MLB JSON data (Teams and Players) into a PostgreSQL database using Python and Docker.

## 📂 Project Structure

Based on the provided files, your directory should look like this:

```text
.
├── database.py           # Main ETL script to insert data into DB
├── docker-compose.yml    # Docker service configuration
├── Dockerfile            # Docker image definition for Postgres
├── init.sql              # SQL schema creation script (required by Dockerfile)
├── teamid.py             # Utility to map Team IDs to Player files
├── verify.py             # Script to verify data integrity
└── Readme.md             # This documentation
```

-----

## 🚀 Prerequisites

Before running the project, ensure you have the following installed:

1.  **Docker Desktop** (for running the database container).
2.  **Python 3.x**.
3.  **Python Libraries**: Install the required driver for PostgreSQL.
    ```bash
    pip install psycopg2-binary
    ```

-----

## 🛠️ Step 1: Start the Database

[cite\_start]We use Docker to spin up a PostgreSQL instance with the correct user, password, and database name automatically configured[cite: 1].

1.  Open your terminal in the project folder.
2.  Run the following command to build and start the container:
    ```bash
    docker-compose up --build -d
    ```
3.  **Configuration Details**:
      * **Port**: The database is exposed on **host port 5433** (mapped to container port 5432).
      * [cite\_start]**User**: `myuser` [cite: 1]
      * [cite\_start]**Password**: `mypassword` [cite: 1]
      * [cite\_start]**Database**: `baseball_stats` [cite: 1]

> **Note:** Ensure the `init.sql` file exists in the directory. [cite\_start]The `Dockerfile` copies this file to initialize the database tables upon startup[cite: 1].

-----

## 🧹 Step 2: Pre-process Data (Optional)

If your player data is missing `team_id` associations, use `teamid.py` to map Team IDs from team files to player files.

1.  Ensure your data folders follow the structure defined in `teamid.py` (or edit the script to match your paths):
      * `./mlb_team_data`: Contains Team JSON files.
      * `./mlb_player_data_rev`: Contains Player JSON files organized by folder.
2.  Run the script:
    ```bash
    python teamid.py
    ```
      * This script scans team files to build a mapping (e.g., "Arizona Diamondbacks" -\> 109) and updates player JSON files with the correct `team_id`.

-----

## 📥 Step 3: Import Data

Use `database.py` to read the JSON files and insert them into the PostgreSQL database.

1.  Run the script:
    ```bash
    python database.py
    ```
2.  **Input Path**: The script will prompt you to enter the path to your data folder.
      * *Example:* `./mlb_player_data_rev` or `./mlb_team_data`
      * Alternatively, you can pass the path as an argument: `python database.py ./my_data_folder`.
3.  **Process**:
      * The script recursively scans folders for `.json` files.
      * It detects if the file is a **Team** or **Player** file and inserts relevant stats (Hitting, Pitching, Game Logs).
      * It handles data cleaning (converting strings like `-.--` to `None`).

-----

## ✅ Step 4: Verify Data

Use `verify.py` to ensure the data was loaded correctly.

**⚠️ Important Configuration Note:**
The provided `verify.py` is currently configured to look for a remote host (`ashlee.lu.im.ntu.edu.tw`). **Before running**, open `verify.py` and update the `DB_CONFIG` to match your local Docker setup:

```python
# Inside verify.py
DB_CONFIG = {
    "dbname": "baseball_stats",
    "user": "myuser",
    "password": "mypassword",
    "host": "localhost",  # <--- Change this to 'localhost'
    "port": "5433"
}
```

1.  Run the verification script:
    ```bash
    python verify.py
    ```
2.  **Output**:
      * **Row Counts**: Displays total records for Teams, Players, and Stats tables.
      * **Sample Check**: Specifically queries for player **Shohei Ohtani** (ID 660271) and the **Los Angeles Dodgers** (ID 119) to confirm complex stats were inserted correctly.

-----

## ❌ Troubleshooting

  * **Connection Refused**: Ensure Docker is running (`docker ps`) and that you are connecting to port **5433**, not 5432.
  * **Missing Dependencies**: If `import psycopg2` fails, run `pip install psycopg2-binary`.
  * **JSON Errors**: The `database.py` script will print specific error messages if it encounters a corrupted JSON file but will continue processing the rest.