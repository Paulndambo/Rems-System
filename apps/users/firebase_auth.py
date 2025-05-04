from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth as firebase_auth
from apps.users.models import User


class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        # Extract the token from the header
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            raise AuthenticationFailed("Invalid Authorization header format")

        # Verify the token
        try:
            decoded_token = firebase_auth.verify_id_token(token)
        except Exception:
            raise AuthenticationFailed("Invalid Firebase ID token")

        # You can retrieve the user's Firebase UID or other claims here
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        profile_picture = decoded_token.get("picture")

        first_name, last_name = name.split(" ") if name else ("", "")

        # Return the user and token if verified
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "email": email,
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                "profile_picture": profile_picture,
                "firebase_uid": uid,
                "role": "Lister",
            },
        )
        return (user, None)
