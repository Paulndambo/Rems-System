from django.conf import settings
from django.core.files.storage import default_storage
import uuid
import os
from firebase_admin import storage


class FirebaseFilesHandler:
    def __init__(self):
        pass

    def upload_file(self, file_path: str):
        try:
            file_extension = os.path.splitext(file_path)[1]
            unique_filename = f"uploads/{uuid.uuid4()}{file_extension}"
            
            bucket = storage.bucket(settings.FIREBASE_STORAGE_BUCKET)
            blob = bucket.blob(unique_filename)

            blob.upload_from_filename(file_path, predefined_acl='public-read')
            
            # Get public URL
            public_url = blob.public_url
            
            return {
                'public_url': public_url,
                'firebase_path': unique_filename
            }

        except Exception as e:
            raise FirebaseFilesHandlerError(f"Failed to upload file: {str(e)}")
        

class FirebaseFilesHandlerError(Exception):
    """Custom exception for Firebase-related errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
