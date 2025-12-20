#! /usr/bin/python3

'''
Initializes the database to be used for storing prescription information
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
    Script for the creation of databases and tables to be used for storing prescription data
    '''
    def __init__(self):
        # Modified it considering most things are run from the root folder
        db_path = './models/storage/BrokenRx.db'
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
    
    def create_user_database(self, conn):
        '''
        Creates the user database which stores the user specific id, their email address,
        username, and their role
        '''
        try:
            cursor = conn.cursor()

            create_table_query = """
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                is_admin BOOLEAN DEFAULT 0
            );
            """
            
            cursor.execute(create_table_query)
            logger.info("Created Users table")
            
            # Creates Indexes for fast query
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_username ON Users (username);",
                "CREATE INDEX IF NOT EXISTS idx_email ON ip_addresses (email);"
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
            logger.error(f"Error creating Users table: {e}")
            conn.rollback()
            return False
    
    
    def create_prescription_table(self, conn):
        '''
        Creates the database to store information about the prescriptions which
        have been submitted and theor current status
        '''
        try:
            cursor = conn.cursor()

            create_table_query = """
            CREATE TABLE IF NOT EXISTS Prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_dispensed BOOLEAN DEFAULT 0
            );
            """
            
            cursor.execute(create_table_query)
            logger.info("Created Prescriptions table")
            
            # Creates Indexes for fast query
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_userid ON Users (id);"
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
            logger.error(f"Error creating Prescriptions table: {e}")
            conn.rollback()
            return False



    def verify_tables(self, table_name):
        '''
        Verify successful creation of the table
        '''
        table_columns = {
            "Users": [
                    'username','email', 'is_admin'
                ],
            "Prescriptions": [
                    'user_id','file_path', 'status', 'created_at', 'updated_at', 'is_dispensed'
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
                self.create_user_database,
                self.create_prescription_table
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
    print(Fore.BLUE + "🚀 Starting BrokenRx Database Setup...")
    print(Fore.BLUE + "=" * 50)
    
    # Initialize the database setup
    db_setup = DatabaseSetup()

    table_list = [
        'Users', 'Prescriptions'
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
