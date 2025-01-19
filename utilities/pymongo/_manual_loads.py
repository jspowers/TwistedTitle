import logging
import json
from utilities.pymongo.collections.DimMovies import MDBDimMovies
logging.basicConfig(format='%(asctime)s | %(levelname)s: %(message)s', level=logging.INFO)


class ManualLoadDimMovies:
    connection = None
    data = None
    
    def __init__(self):
        pass

    def extract(self):
        # File path to the JSON file
        file_path = "/Users/jamespowers/Dev/TwistedTitle/movies_last_30_years.json"

        # Load the JSON file
        with open(file_path, "r") as file:
            self.data = json.load(file)

    def connect(self): 
        self.connection = MDBDimMovies()
        return
        
    def load(self):
        self.connection.write_db_movie(
            documents=self.data,
            document_key="id",
            overwrite=True
            )