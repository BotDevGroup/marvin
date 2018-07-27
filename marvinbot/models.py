from uuid import uuid5, NAMESPACE_X500
from passlib.context import CryptContext
from marvinbot.utils import localized_date
from marvinbot.defaults import (
    DEFAULT_ROLE, ADMIN_ROLE, OWNER_ROLE,
    POWER_USERS, RoleType
)

import mongoengine

bot_security_context = CryptContext(
    schemes=["bcrypt", ],
    default="bcrypt",)


def hash_password(pwd):
    return bot_security_context.encrypt(pwd)


def verify_password(pwd, hsh):
    return bot_security_context.verify(pwd, hsh)

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
    password = mongoengine.StringField()
    active = mongoengine.BooleanField(default=True)

    # TODO: Implement proper groups
    role = mongoengine.StringField(choices=tuple((role.value, role) for role in RoleType), default=DEFAULT_ROLE.value)
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
    def by_username(cls, username):
        try:
            return cls.objects.get(username=username)
        except cls.DoesNotExist:
            return None

    @classmethod
    def is_user_admin(cls, user_data):
        u = cls.by_id(user_data.id)
        if not u:
            return False
        return u.is_admin()

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

    def check_password(self, password):
        """Check if the password is correct"""
        if not self.password:
            return False
        return self.active and verify_password(password, self.password)

    def change_password(self, new_pass):
        """Encrypts and sets the user's password"""
        self.password = hash_password(new_pass)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def __str__(self):
        return "{id}: {username}".format(id=self.id, username=self.username or '<NoUserName>')
