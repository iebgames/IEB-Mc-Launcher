import json
import os

class Config:
    DEFAULT_CONFIG = {
        "username": "Player",
        "uuid": "",
        "ram": 2048,
        "theme": "Dark",
        "minecraft_dir": os.path.expandvars(r"%APPDATA%\.minecraft"),
        "fps_boost": False,
        "java_path": "java",
        "show_snapshots": False
    }
    
    config_file = "config.json"
    data = {}

    @classmethod
    def load(cls):
        if os.path.exists(cls.config_file):
            try:
                with open(cls.config_file, "r") as f:
                    cls.data = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                cls.data = cls.DEFAULT_CONFIG.copy()
        else:
            cls.data = cls.DEFAULT_CONFIG.copy()
            cls.save()

    @classmethod
    def save(cls):
        try:
            with open(cls.config_file, "w") as f:
                json.dump(cls.data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    @classmethod
    def get(cls, key, default=None):
        return cls.data.get(key, default)

    @classmethod
    def set(cls, key, value):
        cls.data[key] = value
        cls.save()
