from abc import ABCMeta


class PluginMetaclass(ABCMeta):
    def __init__(cls, name, base, attrs):
        super(PluginMetaclass, cls).__init__(cls)

        if not hasattr(cls, 'registered'):
            cls.registered = []
        else:
            cls.registered.append(cls)