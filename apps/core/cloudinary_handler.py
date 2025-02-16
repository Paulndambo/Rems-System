import os
from typing import Dict, Optional
from django.conf import settings
import cloudinary
import cloudinary.uploader
import cloudinary.api

class CloudinaryHandler:
    """Handles image upload operations with Cloudinary service."""
    
    def __init__(self):
        """Initialize Cloudinary credentials from Django settings."""
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET
        self.configure_cloudinary()

    def configure_cloudinary(self) -> None:
        """Configuring Cloudinary with credentials."""
        cloudinary.config(  
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret
        )

    def upload_image(self, image_file: str, folder: str) -> Dict[str, str]:
        try:
            upload_result = cloudinary.uploader.upload(
                file=image_file,
                folder=folder,
                resource_type='image'
            )
            
            return {
                'public_url': upload_result['secure_url'],
                'public_id': upload_result['public_id']
            }
        except Exception as e:
            raise CloudinaryError(f"Failed to upload image: {str(e)}")

    def delete_image(self, public_id: str) -> bool:
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            raise CloudinaryError(f"Failed to delete image: {str(e)}")
        

    def clean_up_temp_file(self, temp_file: str) -> None:
        """Cleaning up the temporary file."""
        try:
            os.remove(temp_file)
        except Exception as e:
            raise CloudinaryError(f"Failed to delete temporary file: {str(e)}")


class CloudinaryError(Exception):
    """Custom exception for Cloudinary-related errors."""
    pass

