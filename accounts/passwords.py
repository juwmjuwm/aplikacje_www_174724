import unicodedata

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PasswordCompositionValidator:
    def validate(self, password, user=None):
        checks = (
            (any(unicodedata.category(character) == 'Ll' for character in password), _('The password must contain a lowercase letter.')),
            (any(unicodedata.category(character) == 'Lu' for character in password), _('The password must contain an uppercase letter.')),
            (any(character.isdecimal() for character in password), _('The password must contain a decimal digit.')),
            (any(unicodedata.category(character).startswith(('P', 'S')) for character in password),
             _('The password must contain a punctuation or symbol character.')),
        )
        errors = [message for valid, message in checks if not valid]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _('Your password must contain a lowercase letter, an uppercase letter, a decimal digit, and a punctuation or symbol character.')
