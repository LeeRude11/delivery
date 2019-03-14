from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class AuthPhoneOrEmailBackend(ModelBackend):

    """
    Authenticate a user who provided either a phone number
    or an email address.
    """
    def authenticate(self, request, username=None, password=None):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(
                Q(phone_number=username) | Q(email=username)
            )
        except user_model.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        else:
            return None
