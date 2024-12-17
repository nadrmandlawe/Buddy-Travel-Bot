from config import MONGODB_URI
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi


from utils import translate

def connect() -> MongoClient:
    """
    This function is connecting to the database, using login and password from bot_secrets file.
    :return: MongoClient
    """
    client = MongoClient(MONGODB_URI, server_api=ServerApi('1'), tls=True, tlsCAFile=certifi.where() )
    return client

# def test_connection():
#     try:
#         client = connect()
#         # List databases to verify connection
#         db_list = client.list_database_names()
#         print("Databases available:", db_list)
#         if db_list:
#             print("Connection successful!")
#         else:
#             print("No databases found.")
#     except Exception as e:
#         print("Connection failed:", str(e))
#
# # Run the connection test
# test_connection()

def get_checklists_collection():
    """
    Get the checklists collection from MongoDB.
    :return: Collection
    """
    client = connect()
    db = client["travel_bot"]
    return db["checklists"]

def get_or_create_checklist(chat_id):
    collection = get_checklists_collection()
    checklist = collection.find_one({"chat_id": chat_id})
    if not checklist:
        # Default checklist items
        default_items = [
            {"name": translate(chat_id, "passport"), "status": "❌"},
            {"name": translate(chat_id, "tickets"), "status": "❌"},
            {"name": translate(chat_id, "boarding_pass"), "status": "❌"},
            {"name": translate(chat_id, "hotel_reservation"), "status": "❌"},
            {"name": translate(chat_id, "travel_insurance"), "status": "❌"}
        ]
        checklist = {"chat_id": chat_id, "items": default_items}
        collection.insert_one(checklist)
    else:
        # Ensure all items are in the correct format
        for i, item in enumerate(checklist["items"]):
            if isinstance(item, str):
                checklist["items"][i] = {"name": item, "status": "❌"}
        collection.update_one({"chat_id": chat_id}, {"$set": {"items": checklist["items"]}})
    return checklist

def add_item_to_checklist(chat_id, item_name):
    collection = get_checklists_collection()
    # Add item in correct format
    new_item = {"name": item_name, "status": "❌"}
    collection.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"items": new_item}}
    )

def delete_item_from_checklist(chat_id, item_name):
    """
    Delete an item from the checklist for a specific chat_id.
    :param chat_id: The chat ID for which the item is deleted.
    :param item: The item to be deleted from the checklist.
    """
    collection = get_checklists_collection()
    collection.update_one(
        {"chat_id": chat_id},
        {"$pull": {"items": {"name": item_name}}}
    )

def update_item_status(chat_id, item_name, status):
    collection = get_checklists_collection()
    collection.update_one(
        {"chat_id": chat_id, "items.name": item_name},
        {"$set": {"items.$.status": status}}
    )