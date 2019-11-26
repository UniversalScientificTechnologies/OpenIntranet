from datetime import datetime

import pymongo
from bson import ObjectId
import warnings

from pymongo.collection import ReturnDocument

from plugins.helpers.database_utils import add_embedded_mdoc_to_mdoc_array, get_mdocument_set_unset_dicts

coll = pymongo.MongoClient().USTintranet.users


def get_users(coll: pymongo.collection.Collection):
    """
    Vrátí list uživatelů z databáze. Každý uživatel má field "_id" s textovou verzí ObjectID jeho mdokumentu.
    """
    users = list(coll.find({'type': 'user'}))
    for user in users:
        user["_id"] = str(user["_id"])
    return users


def get_user(coll: pymongo.collection.Collection, _id: str):
    """
    Vrátí mdokument daného uživatele. Uživatel má field "_id" s textovou verzí ObjectID jeho mdokumentu.
    """
    user = coll.find_one({'_id': ObjectId(_id)})
    user["_id"] = str(user["_id"])
    return user


def get_user_contracts(coll: pymongo.collection.Collection, _id: str, sort_by="signing_date"):
    """
    Vrátí list smluv uživatele seřazených sestupně podle fieldu daného parametrem sort_by.
    """
    cursor = coll.aggregate([
        {"$match": {"_id": ObjectId(_id)}},
        {"$unwind": "$contracts"},
        {"$sort": {f"contracts.{sort_by}": -1}},
        {"$group": {"_id": "$_id", "contracts": {"$push": "$contracts"}}}
    ])
    return next(cursor, {}).get("contracts", [])


def update_user(coll: pymongo.collection.Collection, _id: str, data: dict, embedded_1to1_docs=("name",)):
    """
    Updatuje data existujícího uživatele v databázi. Data by měla být first level fieldy a fieldy jednotlivě embedded
    mdokumentů v dot notation. Pro updatování polí embedded mdokumentů jsou speciální funkce.
    Je-li hodnota určitého fieldu "" (prázdný řetězec), field je z mdokumentu odstraněn (je-li poslední v embedded
    mdokumentu, embedded mdokument je odstraněn).
    """
    to_unset = {key: "" for key, value in data.items() if value == ""}
    for key in to_unset:
        del data[key]

    operation_dict = {}
    if data:
        operation_dict["$set"] = data
    if to_unset:
        operation_dict["$unset"] = to_unset

    updated = coll.find_one_and_update({"_id": ObjectId(_id)}, operation_dict, return_document=ReturnDocument.AFTER)

    for key in embedded_1to1_docs:
        if not updated[key]:
            coll.update_one({"_id": ObjectId(_id)}, {"$unset": {"name": ""}})


def update_user_address(coll: pymongo.collection.Collection, _id: str, address: dict):
    """
    Nastaví pro daného uživatele adresu. Dict address musí obsahovat field "type". Uživatel může mít jen jednu adresu
    daného typu.
    Je-li hodnota určitého fieldu "" (prázdný řetězec) nebo None, field je z adresy odstraněn (je-li poslední v adrese
    kromě "type", je adresa odstraněna).

    """
    address_type = address["type"]

    to_set, to_unset = get_mdocument_set_unset_dicts(address)

    # pokud už je tento typ adresy v databázi
    if coll.find_one({"_id": ObjectId(_id), "addresses.type": address_type}):

        operation_dict = {}
        if len(to_set) > 1:  # je tam něco kromě "type"
            operation_dict["$set"] = {f"addresses.$.{key}": value for key, value in to_set.items()}
        if to_unset:
            operation_dict["$unset"] = {f"addresses.$.{key}": value for key, value in to_unset.items()}

        updated = coll.find_one_and_update({"_id": ObjectId(_id), "addresses.type": address_type}, operation_dict,
                                           return_document=ReturnDocument.AFTER)

        # smaž adresu z "addresses", pokud po updatu obsahuje pouze "type"
        for address in updated["addresses"]:
            if address["type"] == address_type and len(address) <= 1:
                delete_user_address(coll, _id, address_type)

    # jinak přidej adresu do databáze, pokud obsahuje víc než jen "type"
    elif len(address) > 1:
        add_embedded_mdoc_to_mdoc_array(coll, _id, "addresses", address, filter_values=None)


def delete_user_address(coll: pymongo.collection.Collection, _id: str, address_type: str):
    """
    Smaže daný typ adresy z databáze.
    """
    coll.update_one({"_id": ObjectId(_id)},
                    {"$pull": {
                        "addresses": {
                            "type": address_type
                        }
                    }})


def add_users(coll: pymongo.collection.Collection, ids: list = None, n: int = None):
    """
    Přidá nové uživatele do databáze. Do databáze se zapíše jen id a čas vytvoření, ostatní data uživatele je nutno
    přidat pomocí update_user.
    Je možné buď zadat přesná id, která budou přidána do databáze, nebo specifikovat kolik uživatelů přidat, id budou
    vygenerovány automaticky.
    Vrací id přidaných uživatelů.
    """
    if ids:
        oids = [ObjectId(_id) for _id in ids]
    elif n:
        oids = [ObjectId() for _ in range(n)]
        ids = [str(_id) for _id in oids]
    else:
        warnings.warn("Nebyla specifikována žádná id ani počet nových uživatelů. Nic se nestalo.")
        return

    users = [{"_id": _id,
              "created": datetime.now().replace(microsecond=0),
              "type": "user",
              } for _id in oids]
    coll.insert_many(users)

    return ids


def delete_user(coll: pymongo.collection.Collection, _id: str):
    """
    Smaže uživatele z databáze.
    """
    coll.delete_one({"_id": ObjectId(_id)})


def add_user_contract(coll: pymongo.collection.Collection, user_id: str, contract: dict):
    """
    Přidá novou smlouvu daného uživatele. Smlouva dostane vlastní "_id".
    """
    add_embedded_mdoc_to_mdoc_array(coll, user_id, "contracts", contract, str(ObjectId()))


def invalidate_user_contract(coll: pymongo.collection.Collection, user_id: str, contract_id: str):
    """
    Přidá do mdocumentu smlouvy key "invalidated" obsahující aktuální datum. Toto značí zneplatnění smlouvy,
    nelze vzít zpět.
    """
    coll.update_one({"_id": ObjectId(user_id), "contracts._id": contract_id},
                    {"$set": {
                        "contracts.$.invalidated": datetime.now().replace(microsecond=0)
                    }})


def sign_user_contract(coll: pymongo.collection.Collection, user_id: str, contract_id: str):
    """
    Nastaví key smlouvy "is_signed" na true.
    """
    coll.update_one({"_id": ObjectId(user_id), "contracts._id": contract_id},
                    {"$set": {
                        "contracts.$.is_signed": True
                    }})


def add_user_document(coll: pymongo.collection.Collection, user_id: str, document: dict):
    """
    Přidá nový dokument daného uživatele. Dokument dostane vlastní "_id".
    """
    _id = str(ObjectId())
    add_embedded_mdoc_to_mdoc_array(coll, user_id, "documents", document, _id)
    return _id


def delete_user_document(coll: pymongo.collection.Collection, user_id: str, document_id: str):
    """
    Smaže daný dokument uživatele z databáze.
    """
    coll.update_one({"_id": ObjectId(user_id)},
                    {"$pull": {
                        "documents": {
                            "_id": document_id
                        }
                    }})


def update_user_document(coll: pymongo.collection.Collection, user_id: str, document_id: str, document: dict):
    """
    Upraví dokument s daným document_id daného uživatele. Má-li field hodnotu "" (prázdný řetězec) nebo None,
    je z mdokumentu odstraněn.
    """
    to_set, to_unset = get_mdocument_set_unset_dicts(document)

    operation_dict = {}
    if to_set:  # některý z fieldů je neprázdný
        operation_dict["$set"] = {f"documents.$.{key}": value for key, value in to_set.items()}
    if to_unset:
        operation_dict["$unset"] = {f"documents.$.{key}": value for key, value in to_unset.items()}

    assert not (set(to_set.keys()).intersection(set(to_unset.keys())))
    print("to_set", to_set)
    print("to_unset", to_unset)

    updated = coll.find_one_and_update({"_id": ObjectId(user_id), "documents._id": document_id}, operation_dict,
                                       return_document=ReturnDocument.AFTER)
    if not list(updated):
        raise ValueError("Uživatel nemá dokument s tímto _id")


def get_user_active_contract(coll: pymongo.collection.Collection, user_id: str):
    now = datetime.now()

    cursor = coll.find({
        "_id": ObjectId(user_id),
        "contracts": {
            "$elemMatch": {
                "valid_from": {"$lte": now},
                "valid_until": {"$gte": now},
                "invalidated": {"$exists": False}
            }
        }
    }, {"contracts.$": 1})

    contracts = next(cursor, {}).get("contracts", {})

    return next(iter(contracts), None)