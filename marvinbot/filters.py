from marvinbot.cache import cache
from telegram.ext.filters import BaseFilter
import re


class RegexpFilter(BaseFilter):
    def __init__(self, pattern, mode='match', **options):
        """Takes a pattern, and returns a match object if it complies.

        Support caching."""
        if mode not in ['match', 'search']:
            raise ValueError('Mode should be either match or search')
        self.mode = mode
        self.pattern = re.compile(pattern, **options)
        self.plain_pattern = pattern

    def filter(self, message):
        return bool(self.pattern.match(message.text))

    # @cache.cache_on_arguments()
    # def __call__(self, expression):
    #     func = getattr(self.pattern, self.mode)
    #     return func(expression)
    #
    # def cache_hash(self):
    #     return self.plain_pattern


class MultiRegexpFilter(RegexpFilter):
    def __init__(self, patterns, **kwargs):
        """Takes a group of patterns and evaluates them.

        If patterns is a dict, add a capture group for each pattern."""
        super(MultiRegexpFilter, self).__init__(self.build_pattern(patterns), **kwargs)

    @staticmethod
    def build_pattern(patterns):
        if isinstance(patterns, dict):
            return "({})".format('|'.join([r'(?P<{name}>{pattern})'.format(name=name,
                                                                           pattern=pattern)
                                           for name, pattern in patterns.items()]))
        elif isinstance(patterns, list):
            return "({})".format('|'.join(patterns))
