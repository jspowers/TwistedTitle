import os 
import logging
logging.basicConfig(format='%(asctime)s | %(levelname)s: %(message)s', level=logging.NOTSET)
from flask_sqlalchemy import SQLAlchemy

twisted_db = SQLAlchemy()

from flask import g
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv
load_dotenv()

class MongoClientWrapper:
    def __init__(self):
        uri = os.getenv('mongoConnection', 'mongoConnection Path Not Found')
        if uri == 'mongoConnection Path Not Found':
            logging.error("Mongo Connection Path Not Found")
            raise Exception("Mongo Connection Path Not Found")
        self.uri = uri


    def init_app(self, app): 
        """
        Initialize the MongoDB connection
        """
        self.client = MongoClient(self.uri,tlsCAFile=certifi.where())
        try:
            self.client.admin.command('ping')
            logging.info("Pinged MongoDB deployment. Successfully connected to MongoDB.")
        except Exception as e:
            logging.error("Exception raise:")
            logging.error(e)
        
    def get_mongo_db(self, database_name):
        if 'db' not in g:
            g.db = self.client[database_name]
        return g.db
    
    def close_connection(self, error=None):
        db = g.pop('db', None)
        if db is not None:
            logging.info(f"Closing MongoDB connection for {db}")
            # self.client.close()
        else :
            logging.info("No MongoDB connection to close")



mongo_client = MongoClientWrapper()
    