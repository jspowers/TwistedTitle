from utilities.pymongo.pymongo_operators import (mongo_get, mongo_get_many, mongo_set, mongo_set_many, mongo_delete)
from extensions import mongo_client
import logging

logging.basicConfig(format='%(asctime)s | %(levelname)s: %(message)s', level=logging.NOTSET)
"""
DB Class: MDBDimMovies
MongoDB Fields: 
    _id : ObjectId
    popularity : float
    release_date : str
    genre_ids : list[int]
    title : str
    id : int
    adult : bool
    vote_count : int   
    vote_average : float
    difficulty : int
    admin_ind_has_clue : bool
    admin_ind_twisted_depri : bool


Methods:
    get_db_user_profile()
    write_db_user_profile()
    remove_db_user_profile() 
"""

class MDBDimMovies(object):
    DB_NAME = "Twisted"
    COLLECTION_NAME = "DimMovies"
    
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
    
    def get_db_movie(self, document_key = "id", ref_id=None, *args, **kwargs):
        """
        Get movie from MongoDB
        """

        if ref_id == None:
            movies = mongo_get_many(
                collection=self.collection,
                **kwargs
            )
            return movies

        else:
            movie = mongo_get(
                primary_key=document_key,
                ref_id=ref_id,
                collection=self.collection,
            )
            
            return movie
    
    def write_db_movies(self, documents, document_key="id",overwrite=False):
        """
        Write movie to MongoDB
        """
        mongo_set_many(
            primary_key=document_key,
            collection=self.collection,
            insert_documents=documents,
            overwrite=overwrite
        )
        return
    
    def write_db_movie(self, document, document_key="id",overwrite=False):
        """
        Update one movie
        """
        mongo_set(
            primary_key=document_key,
            ref_id=document[document_key],
            insert_document=document,
            collection=self.collection,
            overwrite=overwrite,
        )
        return
    
    
    def remove_db_movie(self,document_key="id"):
        """
        Remove movie from MongoDB
        """
        mongo_delete(
            primary_key=document_key,
            ref_id=self.mongo_user_id,
            collection=self.collection,
        )
        return