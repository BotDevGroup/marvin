from .message import MessageView


class InfoView(MessageView):

    def __init__(self, message):
        super().__init__(message)

    def __repr__(self):
        return "ℹ {0}".format(self.message)

    def __str__(self):
        return "ℹ {0}".format(self.message)
