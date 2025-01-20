from pymongo import ReturnDocument, InsertOne, ReplaceOne
import logging

logging.basicConfig(
    format="%(asctime)s | %(levelname)s: %(message)s", level=logging.NOTSET
)

"""
PyMongo Introduction
https://pymongo.readthedocs.io/en/stable/tutorial.html

Creating reusable functions that can read/write to MongoDB
"""

def mongo_get(collection, primary_key, ref_id):
    mongo_record = collection.find_one({primary_key: ref_id})
    if mongo_record == None:
        logging.warning(f"Mongo Record for {primary_key}: {ref_id} was not found.")
        return
    return mongo_record


def mongo_get_many( collection, key=None, ref_id=None, *args, **kwargs):
    logging.info(f"Getting records from MongoDB baseed on {key}: {ref_id}. Additional args {args} and kwargs {kwargs}")
    limit = 100 if kwargs.get("limit", None) == None else kwargs.get("limit")
    mongo_records = collection.find(
        filter=kwargs.get("filter", {}),
        sort=kwargs.get("sort", {}),
        limit=limit
        )
    if mongo_records == None:
        logging.warning(f"Mongo Records were not found.")
        return
    return mongo_records


def mongo_set(primary_key, ref_id, collection, insert_document, overwrite=False):
    mongo_record = collection.find_one({primary_key: ref_id})
    mongo_id = mongo_record[primary_key] if mongo_record != None else None
    if mongo_id == None:
        logging.info(
            f"Mongo ID ({ref_id}) not found in collection. record will be created."
        )
    # Update (or insert) profile when overwrite is set to true
    # 1) Mongo record found and overwrite set to true OR if profile wasn't found
    if overwrite == True or mongo_id == None:
        inserted_id = collection.find_one_and_replace(
            filter={primary_key: ref_id},
            replacement=insert_document,
            upsert=True,  # Insert if document doesn't exists
            return_document=ReturnDocument.AFTER,
        )[primary_key]
        if inserted_id == None:
            logging.error("failed to update/write User document")
            return
        else:
            logging.info(
                f"wrote document to Mongo Collection with primary key: {inserted_id}"
            )
            return
    # Log warning that user already exists and overwrite set to false
    elif overwrite == False and mongo_id != None:
        logging.warning(
            f"no update/insert made. record for '{mongo_id}' already exists and Overwrite == False."
        )
        return
    logging.info("Updating actions completed")
    return


def mongo_set_many(
    primary_key: str,
    collection: str,
    insert_documents: list[dict],
    overwrite=False,
) -> None:
    """
    Bulk write documents to a MongoDB collection.
    """

    logging.info(
        f"OVERWRITE: {overwrite} - Command to bulk write to {collection}: {len(insert_documents)} records."
    )

    # find records that already exist to split the population of records to be inserted
    search_refs = [doc[primary_key] for doc in insert_documents]
    doc_search = collection.find(
        filter={primary_key: {"$in": search_refs}},
        projection={primary_key: True},
    )

    existing_docs = set([doc[primary_key] for doc in doc_search])

    # Create Requests bank
    requests = []

    # if the requests are set to overwrite, instantiate ReplaceOne jobs
    if overwrite:
        for doc in insert_documents:
            ref_id = doc[primary_key]
            requests.append(
                ReplaceOne(
                    filter={primary_key: ref_id},
                    replacement=doc,
                    upsert=True,
                )
            )

    # if no overwrite, only create InsertJobs
    else:
        requests += [
            InsertOne(document=doc)
            for doc in insert_documents
            if doc[primary_key] not in existing_docs
        ]

    logging.info(f'Number of bulk write requests to make: {len(requests)}')
    result = collection.bulk_write(requests)
    logging.info(
        f"Inserted Count: {result.inserted_count} // Deleted Count: {result.deleted_count} // Modified Count: {result.modified_count}"
    )
    return


def mongo_delete(primary_key, ref_id, collection):
    if ref_id == None:
        logging.warning("No referenece ID provided, skipping delete")
        return
    mongo_record = collection.find_one({primary_key: ref_id})
    mongo_record_item = mongo_record[primary_key] if mongo_record != None else None
    count = collection.delete_many({primary_key: mongo_record_item}).delete_count
    if count <= 0 or count == None:
        logging.warning("No records deleted from collection")
    else:
        logging.info(
            f"Mongo record {primary_key}: {mongo_record_item} removed from Collection."
        )
    return