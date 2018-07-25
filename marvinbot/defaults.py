from enum import Enum

DEFAULT_PRIORITY = 2

class RoleType(Enum):
    ADMIN = 'admin'
    OWNER = 'owner'
    NORMAL = 'normal'

DEFAULT_ROLE = RoleType.NORMAL
ADMIN_ROLE = RoleType.ADMIN
OWNER_ROLE = RoleType.OWNER

POWER_USERS = [RoleType.OWNER, RoleType.ADMIN]
