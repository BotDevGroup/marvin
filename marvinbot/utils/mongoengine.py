from mongoengine.base import BaseField

# Blatantly copied from https://github.com/MongoEngine/extras-mongoengine
class EnumField(BaseField):

    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        kwargs['choices'] = [choice for choice in enum]
        super(EnumField, self).__init__(*args, **kwargs)

    def __get_value(self, enum):
        return enum.value if hasattr(enum, 'value') else enum

    def to_python(self, value):
        return self.enum(super(EnumField, self).to_python(value))

    def to_mongo(self, value):
        return self.__get_value(value)

    def prepare_query_value(self, op, value):
        return super(EnumField, self).prepare_query_value(
            op, self.__get_value(value))

    def validate(self, value, **kwargs):
        return super(EnumField, self).validate(self.__get_value(value))

    def _validate(self, value, **kwargs):
        return super(EnumField, self)._validate(
            self.enum(self.__get_value(value)), **kwargs)