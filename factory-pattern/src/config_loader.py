import yaml

class ConfigLoader:

    _config = None

    @classmethod
    def load(cls, path="config.yaml"):
        if cls._config is None:
            with open(path, "r") as f:
                cls._config = yaml.safe_load(f)
        return cls._config

    @classmethod
    def get(cls, *keys):
        config = cls.load()
        value = config
        for key in keys:
            value = value[key]
        return value