from telegram.ext import filters
from config import settings

class AdminFilter(filters.BaseFilter):
    def filter(self, message):
        return message.from_user.id in settings.ADMIN_IDS

admin_filter = AdminFilter()