from requests_oauthlib import OAuth2Session
from typing import Optional
from uuid import uuid5, NAMESPACE_X500
from passlib.context import CryptContext
from marvinbot.utils import localized_date
from marvinbot.utils.mongoengine import EnumField
from marvinbot.defaults import (
    DEFAULT_ROLE, ADMIN_ROLE, OWNER_ROLE,
    POWER_USERS, RoleType
)

import mongoengine

bot_security_context = CryptContext(
    schemes=["bcrypt", ],
    default="bcrypt",)


def hash_password(pwd: str):
    return bot_security_context.encrypt(pwd)


def verify_password(pwd: str, hsh: str):
    return bot_security_context.verify(pwd, hsh)


def make_token(user: 'User'):
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
    role = EnumField(RoleType, default=DEFAULT_ROLE)
    banned = mongoengine.BooleanField(default=False)
    auth_token = mongoengine.StringField()

    oauth_credentials = mongoengine.DictField()

    def is_admin(self) -> bool:
        # TODO: Actually check groups
        return self.role in POWER_USERS

    @classmethod
    def by_id(cls, user_id: int) -> Optional['User']:
        try:
            return cls.objects.get(id=user_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def by_username(cls, username: str) -> Optional['User']:
        try:
            return cls.objects.get(username=username)
        except cls.DoesNotExist:
            return None

    @classmethod
    def is_user_admin(cls, user_data) -> bool:
        u = cls.by_id(user_data.id)
        if not u:
            return False
        return u.is_admin()

    @classmethod
    def from_telegram(cls, user_data, save=False) -> (Optional['User'], bool):
        prev = cls.by_id(user_data.id)
        if prev:
            return prev, False
        user = cls(id=user_data.id, first_name=user_data.first_name, last_name=user_data.last_name,
                   username=user_data.username)
        if save:
            user.save()
        return user, True

    def check_password(self, password: str) -> bool:
        """Check if the password is correct"""
        if not self.password:
            return False
        return self.active and verify_password(password, self.password)

    def change_password(self, new_pass: str):
        """Encrypts and sets the user's password"""
        self.password = hash_password(new_pass)

    def store_token(self, client_config: 'OAuthClientConfig', token: dict):
        if client_config.name not in self.oauth_credentials:
            self.oauth_credentials[client_config.key] = []
        self.oauth_credentials[client_config.key].append(token)

    def get_token(self, client_config: 'OAuthClientConfig', index: int = 0) -> dict:
        return self.oauth_credentials.get(client_config.name, []).get(index)

    def is_authenticated(self) -> bool:
        return True

    def is_active(self) -> bool:
        return self.active

    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return self.username

    def __str__(self):
        return "{id}: {username}".format(id=self.id, username=self.username or '<NoUserName>')


class OAuthClientKey(mongoengine.EmbeddedDocument):
    plugin_name = mongoengine.StringField(required=True)
    client_name = mongoengine.StringField(required=True)

    def __str__(self):
        return "|".join([self.plugin_name, self.client_name])


class OAuthClientConfig(mongoengine.Document):
    client_key = OAuthClientKey(primary_key=True)
    client_id = mongoengine.StringField(required=True)
    client_secret = mongoengine.StringField(required=True)
    authorization_url = mongoengine.URLField(required=True)
    token_url = mongoengine.URLField(required=True)
    default_scopes = mongoengine.ListField(mongoengine.StringField())

    @classmethod
    def by_name(cls, plugin_name: str, client_name: str) -> Optional['OAuthClientConfig']:
        try:
            key = OAuthClientKey(plugin_name=plugin_name, client_name=client_name)
            return cls.objects.get(client_key=key)
        except cls.DoesNotExist:
            return None

    def make_session(self, token) -> OAuth2Session:
        """Make a session for the current service using token

        :param token: The token
        :return: a Session object"""
        if token:
            client = OAuth2Session(self.client_id, token=token)
            return client
        else:
            raise ValueError("No auth_token for this client.")

    def get_session(self, user: User, index: int = 0) -> OAuth2Session:
        """Generate a requests.Session object preconfigured with oauth2 credentials.

        :param user: the user to make the session for
        :param index: if multiple tokens are available, specify which in order
        :returns: a Session object
        """
        if user is None:
            raise ValueError('user is required')
        if self.name in user.oauth_credentials:
            token = user.get_token(self, index)
            return self.make_session(token)
        else:
            raise ValueError(f'No [{self.name}] credentials available in {user}')

    @property
    def key(self) -> str:
        return str(self.client_key)
