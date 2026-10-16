from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def canonical_username(username):
    return AbstractBaseUser.normalize_username(username).casefold()


def validate_username(username):
    validator = UnicodeUsernameValidator()
    validator(username)
    canonical = canonical_username(username)
    if len(username) > 150 or len(canonical) > 150:
        raise ValidationError('Ensure this value has at most 150 characters.')
    validator(canonical)
    return canonical
