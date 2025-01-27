from firebase_admin import firestore

def write_to_firebase(collection, data):
    db = firestore.client()
    db.collection(collection).add(data)

def write_to_firebase_with_id(collection, data):
    db = firestore.client()
    db.collection(collection).add(data)
    return db.collection(collection).document().id
