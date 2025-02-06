from typing import Optional
from pydantic import BaseModel
from extensions import mongo_client
from bson import ObjectId
import logging

logging.basicConfig(format='%(asctime)s | %(levelname)s: %(message)s', level=logging.NOTSET)
"""
DB Class: MDBDimCLues
MongoDB Fields:
    _id : ObjectId
    (fk) movie_id : int
    original_title : str
    twisted_title : str
    raw_twisted_title : str
    description : str
    origin : enum
    admin_validated : bool
    admin_edited : bool
    edit_history : dict[version:description
    description_contains_title : bool
    created_unixtime : int
"""

class Clue(BaseModel):
    """
    Default Schema for Twisted Title Clues
    """
    _id : ObjectId
    movie_id: int
    original_title: str
    twisted_title: str
    raw_twisted_title: str
    description: str
    origin: str
    admin_validated: bool
    admin_edited: bool
    edit_history: Optional[dict[str,str]]
    description_contains_title: bool
    created_unixtime: int
    updated_unixtime: Optional[int]

class MDBDimClues(object):
    DB_NAME = "Twisted"
    COLLECTION_NAME = "DimClues"
    
    
    def __init__(self):
        self.db = mongo_client.get_mongo_db(self.DB_NAME)
        return

    def __enter__(self):
        self.collection = self.db[self.COLLECTION_NAME]
        logging.info(f"Opened Collection: {self.DB_NAME}.{self.COLLECTION_NAME}")
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.collection = None
        logging.info(f"Closed Collection: {self.DB_NAME}.{self.COLLECTION_NAME}")
        return