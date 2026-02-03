import json
import os
import uuid

class ProfileManager:
    profiles_file = "profiles.json"
    profiles = []
    current_profile = None

    @classmethod
    def load(cls):
        if os.path.exists(cls.profiles_file):
            try:
                with open(cls.profiles_file, "r") as f:
                    data = json.load(f)
                    cls.profiles = data.get("profiles", [])
                    cls.current_profile = data.get("current_profile", None)
            except:
                cls.profiles = []
                cls.current_profile = None
        
        if not cls.profiles:
            # Create default profile
            default_profile = {
                "id": str(uuid.uuid4()),
                "name": "Player",
                "uuid": str(uuid.uuid4()), # Offline UUID
                "type": "offline"
            }
            cls.profiles.append(default_profile)
            cls.current_profile = default_profile["id"]
            cls.save()

    @classmethod
    def save(cls):
        data = {
            "profiles": cls.profiles,
            "current_profile": cls.current_profile
        }
        with open(cls.profiles_file, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def get_current_profile_data(cls):
        for p in cls.profiles:
            if p["id"] == cls.current_profile:
                return p
        return cls.profiles[0] if cls.profiles else None

    @classmethod
    def create_profile(cls, name):
        new_profile = {
            "id": str(uuid.uuid4()),
            "name": name,
            "uuid": str(uuid.uuid4()),
            "type": "offline"
        }
        cls.profiles.append(new_profile)
        cls.current_profile = new_profile["id"]
        cls.save()
        return new_profile
