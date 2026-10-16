from django.contrib.auth.backends import ModelBackend

from .usernames import canonical_username


class CanonicalUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
        if username is not None:
            username = canonical_username(username)
        return super().authenticate(request, username=username, password=password, **kwargs)
