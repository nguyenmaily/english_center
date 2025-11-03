from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.settings import api_settings
from django.core.cache import cache

from .models import UserAccount


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication with blacklist functionality
    """
    
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        try:
            user = UserAccount.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except UserAccount.DoesNotExist:
            raise InvalidToken('User not found')

        if not user.is_active:
            raise InvalidToken('User is inactive')

        if user.status != 'active':
            raise InvalidToken('User account is not active')

        return user

    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if authentication was successful.
        Otherwise returns `None`.
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        # Check if token is blacklisted
        jti = validated_token.get('jti')
        if self.is_token_blacklisted(jti):
            raise InvalidToken('Token is blacklisted')

        return self.get_user(validated_token), validated_token

    def is_token_blacklisted(self, jti):
        """
        Check if token JTI is blacklisted
        """
        return cache.get(f'blacklisted_token:{jti}', False)
