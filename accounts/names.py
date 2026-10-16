from django.core.exceptions import ValidationError


def normalize_name(value):
    name = value.strip()
    if not name or not all(character.isalpha() for character in name):
        raise ValidationError('Use letters only; the name cannot be blank.')
    result = name.capitalize()
    if len(result) > 150:
        raise ValidationError('Ensure this value has at most 150 characters.')
    return result
