#! /usr/bin/python3

'''
Initializes the databases to be used for authorization server
'''
import logging
from pathlib import Path
import sqlite3
from colorama import Fore

# Initializes the Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseSetup:
    '''
    Script for the creation of databases and tables to be used for authorization
    '''
    def __init__(self):
        # Modified it considering most things are run from the root folder
        db_path = './models/storage/oauthdb.db'
        self.db_path = db_path
        self.db_dir = Path(self.db_path).parent
    
    def create_db_directory(self):
        '''
        Checks if the directory for the database exists and creates it if it does not
        '''
        if self.db_dir and not self.db_dir.exists():
            self.db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created database directory: {self.db_dir}")
    
    def create_connection(self) -> sqlite3.Connection:
        '''
        Creates connection to the database if it does not exist
        '''
        try:
            conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}" + Fore.GREEN)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            return None
    
    def create_authentication_tables(self, conn):
        '''
        Creates tables for storing username and password, authorization codes and oauth client
        informations
        '''
        try:
            cursor = conn.cursor()

            create_user_query = """
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            );
            """
            
            create_oauth_clients = """
            CREATE TABLE IF NOT EXISTS oauth_clients (
                client_id TEXT PRIMARY KEY,
                name TEXT,
                redirect_uri TEXT
            );
            """
            # redirect_uri is the allowed redirect uri's which should be checked and confirmed later on

            create_authorization_codes = """
            CREATE TABLE IF NOT EXISTS authorization_codes (
                code TEXT PRIMARY KEY,
                user_id INTEGER,
                client_id TEXT,
                redirect_uri TEXT,
                code_challenge TEXT,
                expires_at TEXT
            );
            """
            # used INTEGER DEFAULT 0 ==> to check if the authorization token has been used before
            # and if it has been not to be reused

            cursor.execute(create_user_query)
            logger.info("Created Users table")
            cursor.execute(create_oauth_clients)
            logger.info("Created aouth clients table")
            cursor.execute(create_authorization_codes)
            logger.info("Created authorization codes table")
            conn.commit()
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_user_id ON authorization_codes (user_id);"
            ]
            
            for index_query in indexes:
                try:
                    cursor.execute(index_query)
                    logger.debug(f"Created index: {index_query.split()[5]}")
                except sqlite3.Error as e:
                    logger.warning(f"Error creating index: {e}")
                
                conn.commit()
                return True
        
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            conn.rollback()
            return False

    def verify_tables(self, table_name):
        '''
        Verify successful creation of the tables
        '''
        table_columns = {
            "Users": [
                    'username', 'password_hash', 'role'
                ],
            "oauth_clients": [
                    'client_id', 'name', 'redirect_uri'
                ],
            "authorization_codes": [
                    'code','user_id', 'client_id', 'redirect_uri', 'code_challenge', 'expires_at'
                ]
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}';
            """

            cursor.execute(query)
            table_exists = cursor.fetchone() is not None

            if table_exists:
                query_pragm = f"PRAGMA table_info({table_name});"
                cursor.execute(query_pragm)
                columns = [col[1] for col in cursor.fetchall()]
                
                expected_columns = table_columns[table_name]

                missing_columns = set(expected_columns) - set(columns)
                if missing_columns:
                    logger.error(f"Missing columns: {missing_columns}")
                    return False
            
            conn.close()
            return table_exists and not missing_columns
            
        except sqlite3.Error as e:
            logger.error(f"Verification failed: {e}")
            return False
    def setup_database(self):
        '''
        Set up the database and creates the table
        '''
        try:
            
            self.create_db_directory()
            conn = self.create_connection()
            if conn is None:
                return False

            table_creators = [
                self.create_authentication_tables
            ]

            success = all(creator(conn) for creator in table_creators)

            conn.close()
            return success

        except Exception as e:
            logger.error(f"Failed to set up database: {e}")
            return False
def main():
    '''
    Setup database and verify
    '''
    print(Fore.BLUE + "🚀 Starting BrokenRx Authentication server Setup...")
    print(Fore.BLUE + "=" * 50)
    
    # Initialize the database setup
    db_setup = DatabaseSetup()

    table_list = [
        'Users', 'oauth_clients', 'authorization_codes'
    ]
    
    # Create the database and table
    if db_setup.setup_database():
        print(Fore.YELLOW + "\n ✅ Database setup completed successfully!" + Fore.CYAN)
        
        for table in table_list:
            if db_setup.verify_tables(table):
                print(f"\n🎯 {table} table verification completed successfully")
            else:
                print(f"❌ {table} table verification failed!")
                print("Please check the logs for details.")
    else:
        print("❌ Database setup failed!")
        print("Please check the logs for details.")

if __name__ == "__main__":
    main()
