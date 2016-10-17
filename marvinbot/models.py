from uuid import uuid5, NAMESPACE_X500
from marvinbot.utils import localized_date
from marvinbot.defaults import (
    USER_ROLES, DEFAULT_ROLE, ADMIN_ROLE, OWNER_ROLE,
    POWER_USERS
)
import mongoengine


def make_token(user):
    date = localized_date()
    # Automatically expires different after an hour
    return str(uuid5(NAMESPACE_X500, "-".join([str(user.id), user.username,
                                               date.strftime('%Y%m%d%h')])))


class User(mongoengine.Document):
    id = mongoengine.LongField(primary_key=True)
    first_name = mongoengine.StringField()
    last_name = mongoengine.StringField()
    username = mongoengine.StringField()

    # TODO: Implement proper groups
    role = mongoengine.StringField(choices=USER_ROLES, default=DEFAULT_ROLE)
    banned = mongoengine.BooleanField(default=False)
    auth_token = mongoengine.StringField()

    def is_admin(self):
        # TODO: Actually check groups
        return self.role in POWER_USERS

    @classmethod
    def by_id(cls, user_id):
        try:
            return cls.objects.get(id=user_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def from_telegram(cls, user_data, save=False):
        prev = cls.by_id(user_data.id)
        if prev:
            return prev, False
        user = cls(id=user_data.id, first_name=user_data.first_name, last_name=user_data.last_name,
                   username=user_data.username)
        if save:
            user.save()
        return user, True

    def __str__(self):
        return "{id}: {username}".format(id=self.id, username=self.username or '<NoUserName>')
