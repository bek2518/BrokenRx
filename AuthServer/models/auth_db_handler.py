#! /usr/bin/python3

'''
Handles all the insertion of data into the database
'''

import sqlite3
import logging

logger = logging.getLogger(__name__)

class DatabaseHandler:
    '''
    Class which handles connection creation and insertion of data to the database
    '''
    def __init__(self):
        self.db_path = './models/storage/oauthdb.db'
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return self
        except Exception as e:
            logger.error(f"Failed to open database connection: {e}")
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            if exc_type is not None:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()

    def store_users(self, username, password_hash):
        '''
        Stores user information into users table
        '''
        role = "user"
        self.cursor.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        )
        
        if self.cursor.fetchone():
            return "username exists"
        
        try:
            self.cursor.execute("""
                INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)
            """, (username, password_hash, role))

            self.conn.commit()
            return self.cursor.lastrowid

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to insert into table Users: {e}')
            return "Error"

    def retrieve_users(self, username):
        '''
        Checks the username and password from database and retrueves the user
        '''
        try:
            self.cursor.execute("""
                SELECT * FROM Users WHERE username = ?
            """, (username,))

            user = self.cursor.fetchone() 

            if not user:
                return None
            
            return user

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to retrieve user: {e}')
            return None
        
    def retrieve_user_by_id(self, user_id):
        '''
        Retrieves the user by using the user id
        '''
        try:
            self.cursor.execute("""
                SELECT * FROM Users WHERE id = ?
            """, (user_id,))

            user = self.cursor.fetchone() 

            if not user:
                return None
            
            return user

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to retrieve user: {e}')
            return None
        
    def store_admin(self, username, password_hash):
        '''
        Stores user information into users table
        '''
        role = "admin"
        self.cursor.execute(
            "SELECT id FROM Users WHERE username=?",
            (username,)
        )
        
        if self.cursor.fetchone():
            return "username exists"
        
        try:
            self.cursor.execute("""
                INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)
            """, (username, password_hash, role))

            self.conn.commit()
            return self.cursor.lastrowid

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to insert into table Users: {e}')
            return "Error"


    def init_oauth_client(self):
        try:
            logger.warning("INIT OAUTH CLIENT CALLED")

            self.cursor.execute(
                """
                INSERT INTO oauth_clients (client_id, name, redirect_uri)
                VALUES (?, ?, ?)
                """,
                (
                    "BrokenRx_client",
                    "BrokenRx Prescription Systems",
                    "http://localhost:5000/callback"
                )
            )

            logger.warning(f"Rowcount after insert: {self.cursor.rowcount}")

            self.conn.commit()
            logger.warning("COMMIT DONE")

            self.cursor.execute(
                "SELECT * FROM oauth_clients WHERE client_id = ?",
                ("BrokenRx_client",)
            )
            logger.warning(f"Inserted row: {self.cursor.fetchone()}")

            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to insert into table oauth_clients: {e}')
            return False




    def oauth_client(self, client_id):
        '''
        Gets the client from oauth_clients table 
        '''
        try:

            self.cursor.execute(
                "SELECT * FROM oauth_clients WHERE client_id=?",
                (client_id,)
            )
            client = self.cursor.fetchone() 

            if not client:
                return None
            
            return client

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to retrieve oauth client: {e}')
            return None


    def store_authorization_codes(self, code, user_id, client_id, redirect_uri, code_challenge, expires_at):
        '''
        Handles the storage of the authorization code, redirect uri and code challenge
        '''
        try:
            self.cursor.execute(
                """
                INSERT INTO authorization_codes
                (code, user_id, client_id, redirect_uri, code_challenge, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    code,
                    user_id,
                    client_id,
                    redirect_uri,
                    code_challenge,
                    expires_at,
                )
            )
            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to insert into table authorization codes: {e}')
            return False

    def retrieve_authorization_code(self, code):
        '''
        Retrieves the authorization code
        '''
        try:
            self.cursor.execute(
                """
                SELECT * FROM authorization_codes WHERE code=?
                """, (code,)
            )
            auth_code = self.cursor.fetchone()

            if not auth_code:
                return "Invalid Code"
            return auth_code
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to retrieve oauth client: {e}')
            return None
        
    def remove_authorization_code(self, code):
        '''
        Removes the authorization code immediately after use to prevent code reuse and make it single use
        '''
        try:
            self.cursor.execute(
                """
                DELETE FROM authorization_codes WHERE code=?
                """, (code,)
            )

            return True
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f'Unable to Delete Authorization Code: {e}')
            return None
