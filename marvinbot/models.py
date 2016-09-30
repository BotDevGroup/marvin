import mongoengine


class User(mongoengine.Document):
    id = mongoengine.LongField(primary_key=True)
    first_name = mongoengine.StringField()
    last_name = mongoengine.StringField()
    username = mongoengine.StringField()

    # TODO: Implement proper groups
    role = mongoengine.StringField(choices=['mortal', 'elevated', 'admin'], default='mortal')

    def is_admin(self):
        # TODO: Actually check groups
        return self.role == 'admin'

    @classmethod
    def by_id(cls, user_id):
        try:
            return cls.objects.get(id=user_id)
        except cls.DoesNotExist:
            return None

    def __str__(self):
        return "{id}: {username}".format(id=self.id, username=self.username or '<NoUserName>')
