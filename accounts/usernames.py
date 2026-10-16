from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError


def canonical_username(username):
    return AbstractBaseUser.normalize_username(username).casefold()


def validate_username(username):
    if not username or not all(character.isalpha() or character.isdecimal() or character == '_' for character in username):
        raise ValidationError('Enter a valid username. Use letters, decimal digits, and underscores only.')
    canonical = canonical_username(username)
    if len(username) > 150 or len(canonical) > 150:
        raise ValidationError('Ensure this value has at most 150 characters.')
    if not canonical or not all(character.isalpha() or character.isdecimal() or character == '_' for character in canonical):
        raise ValidationError('Enter a valid username. Use letters, decimal digits, and underscores only.')
    return canonical
