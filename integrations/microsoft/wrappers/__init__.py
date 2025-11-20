"""Microsoft Graph API wrappers"""

from .calendar_wrapper import MicrosoftCalendarWrapper
from .mail_wrapper import MicrosoftMailWrapper
from .contacts_wrapper import MicrosoftContactsWrapper

__all__ = [
    'MicrosoftCalendarWrapper',
    'MicrosoftMailWrapper',
    'MicrosoftContactsWrapper',
]
