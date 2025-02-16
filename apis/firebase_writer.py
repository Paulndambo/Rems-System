from firebase_admin import firestore

class FirebaseListingWriter:
    def __init__(self):
        self.db = firestore.client()

    def write_to_firebase_document_with_id(self, collection, data, document_id):
        self.db.collection(collection).document(document_id).set(data)
        return document_id

    def update_firebase_document(self, collection, document_id, data):
        self.db.collection(collection).document(document_id).update(data)


    def delete_firebase_document(self, collection, document_id):
        self.db.collection(collection).document(document_id).delete()


    def add_image_to_firebase(self, collection, document_id, image):
        self.db.collection(collection).document(document_id).collection('images').add(image)

    def update_firebase_document(self, collection, document_id, data):
        self.db.collection(collection).document(document_id).update(data)

    def add_images_to_firebase(collection, document_id, images):
        db = firestore.client()
        db.collection(collection).document(document_id).collection('images').add(images)

    def add_image_to_firebase(collection, document_id, image):
        db = firestore.client()
        db.collection(collection).document(document_id).collection('images').add(image)
