from dogpile.cache.region import make_region
import inspect
import unicodedata


__all__ = ['to_ascii', 'to_str', 'cache_key_generator', 'cache', 'configure_cache',
           'includeme', 'create_cache']


def to_ascii(ze_text):
    return unicodedata.normalize('NFKD', ze_text).encode('ascii', 'ignore')


def to_str(val, transform=to_ascii):
    return transform(val)


def cache_key_generator(namespace, fn, to_str=to_str):
    """Cache key generation function that accepts keyword args"""
    if namespace is None:
        namespace = '%s:%s' % (fn.__module__, fn.__name__)
    else:
        namespace = '%s:%s|%s' % (fn.__module__, fn.__name__, namespace)

    args = inspect.getargspec(fn)
    has_self = args[0] and args[0][0] in ('self', 'cls')

    def generate_key(*args, **kw):
        args = list(args)
        if kw:
            for k in sorted(kw):
                args.append('{}={}'.format(k, to_str(kw[k])))
        if has_self:
            inst = args[0]
            if hasattr(inst, 'cache_hash'):
                hsh = inst.cache_hash()
                args.insert(0, hsh)
            else:
                args = args[1:]

        # Some key manglers don't like non-ascii inputs, normalize
        key = namespace + "|" + " ".join(map(to_str, args))
        return key
    return generate_key


DEFAULT_PREFIX = 'marvinbot.caching.'


DEFAULTS = {
    'backend': 'dogpile.cache.memory',
    'expiration_time': 3600,
}


cache = make_region(function_key_generator=cache_key_generator).configure_from_config(
    {DEFAULT_PREFIX + k: v for k, v in DEFAULTS.items()}, DEFAULT_PREFIX)


def create_cache():
    cache_inst = make_region(function_key_generator=cache_key_generator)
    return cache_inst


def configure_cache(settings, cache_inst=None):
    global cache
    conf = {}
    conf.update({k: v for k, v in DEFAULTS.items()})
    conf.update(settings.get('cache', {}))

    if cache_inst:
        cache = cache_inst
    else:
        cache = create_cache()
    cache.configure_from_config(conf, '')
    return cache


def includeme(config):
    global cache
    # See: http://dogpilecache.readthedocs.org/en/latest/usage.html

    cache = create_cache()
    configure_cache(config)
