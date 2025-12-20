#! /usr/bin/python3

'''
Handles all the insertion of data into the database
'''

import sqlite3
import logging
import os
import uuid

logger = logging.getLogger(__name__)

class DatabaseHandler:
    '''
    Class which handles connection creation and insertion of data to the database
    '''
    def __init__(self):
        self.db_path = './models/storage/BrokenRx.db'
        self.upload_path = "./models/storage/uploads/prescriptions"
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

    def store_users(self, user_id, username, email, is_admin):
        '''
        Stores user information into users database
        '''
        try:
            self.cursor.execute("""
                INSERT INTO Users (id, username, email, is_admin) VALUES (?, ?, ?, ?)
            """, (user_id, username, email, is_admin))

            self.conn.commit()
            return self.cursor.lastrowid

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to insert into table Users: {e}')
            return None
        
    def get_user_profile(self, user_id):
        '''
        Gets the user profile
        '''
        try:
            query = f"SELECT * FROM Users WHERE id = ?"

            self.cursor.execute(query, str(user_id))
            user = self.cursor.fetchall()
            return user
        except Exception as e:
            logger.error(f'Unable to get User information {e}')
            return None    

    def store_prescription(self, user_id, file_storage):
        '''
        Stores prescription information into prescriptions database
        '''
        status = "Unchecked"
        user_dir = os.path.join(self.upload_path, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        extension = os.path.splitext(file_storage["file"].filename)
        filename = f"rx_{uuid.uuid4().hex}_{extension[0]}{extension[1]}"
        file_path = os.path.join(user_dir, filename)

        file_obj = file_storage['file']
        file_obj.save(file_path)

        try:
            self.cursor.execute("""
                INSERT INTO Prescriptions (user_id, file_path, status) VALUES (?, ?, ?)
            """, (user_id, file_path, status))

            self.conn.commit()
            return self.cursor.lastrowid

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to insert into table Prescriptions: {e}')
            return None

    def update_status(self, prescription_id, status):
        '''
        Updates the status of prescription
        '''
        try:
            self.cursor.execute("""
                UPDATE Prescriptions SET status = ? WHERE id = ?
            """, (status, prescription_id))

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f'Failed to update status of prescription: {e}')
            return None

    def aggregate_user_info(self):
        '''
        Gets all users and aggregates them by the number of prescriptions they submitted
        '''
        try:
            query = f"SELECT username, COUNT(*) FROM prescriptions JOIN users ON prescriptions.user_id = users.id GROUP BY username;"

            self.cursor.execute(query)
            aggregate = self.cursor.fetchall()
            return aggregate
        except Exception as e:
            logger.error(f'Unable to aggregate user information')
            return None


    def retrieve_all_prescriptions(self):
        '''
        Only admin functionality which retrieves the prescriptions of all users
        '''
        try:
            query = f"SELECT * FROM Prescriptions"

            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            logger.error(f'Unable to retrieve prescriptions')
            return None

    def retrieve_user_prescription(self, user_id):
        '''
        Retrieves all prescriptions of a specific user
        '''
        try:
            query = f"SELECT * FROM Prescriptions WHERE user_id = ?"

            self.cursor.execute(query, user_id)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            logger.error(f'Unable to retrieve prescriptions for user with the id {user_id}')
            return None
        
    def retrieve_prescription_by_id(self, prescription_id):
        '''
        Retrieves prescription by prescription id
        '''
        try:
            query = f"SELECT * FROM Prescriptions WHERE id = ?"

            self.cursor.execute(query, prescription_id)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            logger.error(f'Unable to retrieve prescription with the prescription id {prescription_id}')
            return None

    def retrieve_prescription_path(self, prescription_id):
        '''
        Retrieves the path for a prescription based on the prescription id
        '''
        try:
            query = f"SELECT file_path FROM Prescriptions WHERE id = ?"

            self.cursor.execute(query, prescription_id)
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            logger.error(f'Unable to retrieve prescription path for prescription with the id {prescription_id}')
            return None