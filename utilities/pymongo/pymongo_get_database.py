from pymongo import MongoClient
import certifi
import logging
logging.basicConfig(format='%(asctime)s | %(levelname)s: %(message)s', level=logging.NOTSET)

import os 
from dotenv import load_dotenv
load_dotenv()

def open_twisted_db():

    uri = os.getenv('mongoConnection', 'mongoConnection Path Not Found')
    if uri == 'mongoConnection Path Not Found':
        logging.error("Mongo Connection Path Not Found")
        raise Exception("Mongo Connection Path Not Found")
    
    # Create a new client and connect to the server
    client = MongoClient(uri,tlsCAFile=certifi.where())
    # Send a ping to confirm a successful connection

    try:
        client.admin.command('ping')
        logging.info("Pinged deployment. Successfully connected to MongoDB.")
    except Exception as e:
        logging.error("Exception raise:")
        logging.error(e)
    return client

# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":     
   # Get the database
   dbname = open_twisted_db()