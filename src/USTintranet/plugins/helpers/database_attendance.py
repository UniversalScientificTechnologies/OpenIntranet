from datetime import datetime

import pymongo
from bson import ObjectId

from plugins.helpers.database_utils import add_embedded_mdoc_to_mdoc_array, get_user_embedded_mdoc_by_id


def add_user_workspan(database, user, workspan):
    workspan_id = str(ObjectId())

    add_embedded_mdoc_to_mdoc_array(database.users, user, "workspans", workspan, workspan_id, filter_values=())

    return workspan_id


def add_user_vacation(database, user, vacation):
    vacation_id = str(ObjectId())

    add_embedded_mdoc_to_mdoc_array(database.users, user, "vacations", vacation, vacation_id)

    return vacation_id


def get_user_workspans(database, user, from_date: datetime, to_date: datetime):
    cursor = database.users.aggregate([
        {"$match": {"user": user}},
        {"$unwind": "$workspans"},
        {"$match": {
            "workspans.from": {
                "$gte": from_date,
                "$lt": to_date,
            }
        }},
        {"$sort": {"workspans.from": 1}},
        {"$group": {"_id": "$_id", "workspans": {"$push": "$workspans"}}}
    ])

    return next(cursor, {}).get("workspans", [])


def get_user_vacations(database,
                       user: str,
                       earliest_end: datetime,
                       latest_end: datetime = None):
    earliest_latest_dict = {
        "$gte": earliest_end
    }
    if latest_end:
        earliest_latest_dict["$lt"] = latest_end

    cursor = database.users.aggregate([
        {"$match": {"user": user}},
        {"$unwind": "$vacations"},
        {"$match": {
            "vacations.to": earliest_latest_dict
        }},
        {"$sort": {"vacations.to": 1}},
        {"$group": {"_id": "$_id", "vacations": {"$push": "$vacations"}}}
    ])

    return next(cursor, {}).get("vacations", [])


def get_user_vacation_by_id(database, user: str, vacation_id: str):
    return get_user_embedded_mdoc_by_id(database, user, "vacations", vacation_id)


def interrupt_user_vacation(database, user, vacation_id, new_end_date):
    database.users.update_one({"user": user, "vacations._id": vacation_id},
                              {"$set": {
                                  "vacations.$.to": new_end_date,
                              }})


def delete_user_workspan(database, user, workspan_id):
    database.users.update_one({"user": user},
                              {"$pull": {
                                  "workspans": {
                                      "_id": workspan_id
                                  }
                              }})
