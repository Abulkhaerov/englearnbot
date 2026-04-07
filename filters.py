from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union
from db import *



class IsAdminFilter(BaseFilter):
    """
    Filter that checks if user is a bot admin.

    Usage:
        @router.message(IsAdminFilter())  # Only admins
        @router.message(IsAdminFilter(is_admin=False))  # Only non-admins
    """

    def __init__(self, is_admin: bool = True) -> None:
        """
        Args:
            is_admin: If True, only admins pass. If False, only non-admins pass.
        """
        self.is_admin = is_admin

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:

        if event.from_user is None:
            return False

        user_is_admin = is_admin(event.from_user.id)

        if self.is_admin:
            return user_is_admin
        return not user_is_admin


class IsWhitelistedFilter(BaseFilter):
    """
    Filter that checks if user is whitelisted.

    Usage:
        @router.message(IsWhitelistedFilter())  # Only whitelisted
        @router.message(IsWhitelistedFilter(is_admin=False))  # Only non-whitelisted
    """

    def __init__(self, is_whitelisted: bool = True) -> None:
        """
        Args:
            is_whitelisted: If True, only whitelisted pass. If False, only non-whitelisted pass.
        """
        self.is_whitelisted = is_whitelisted

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:

        if event.from_user is None:
            return False

        user_is_whitelisted = is_whitelisted(event.from_user.id)

        if self.is_whitelisted:
            return user_is_whitelisted
        return not user_is_whitelisted

