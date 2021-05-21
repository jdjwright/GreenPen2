from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


def validate_g_sheet(url):
    if not re.search(r'(^https://docs.google.com/spreadsheets/.*/edit?)', url):
        raise ValidationError(
            _('%(url)s is not a Google Sheets URL'),
            params={'url': url},
        )


def validate_g_form(url):
    if not re.search(r'(^https://docs.google.com/forms/.*)', url):
        raise ValidationError(
            _('%(url)s is not a Google Sheets URL'),
            params={'url': url},
        )