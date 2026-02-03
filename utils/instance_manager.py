import os
import json
import shutil
from .config import Config

class InstanceManager:
    INSTANCES_FILE = "instances.json"

    @staticmethod
    def get_instances_dir():
        # Store instances in a subdirectory of the main app or minecraft dir
        # For simplicity, let's use <minecraft_dir>/instances
        mc_dir = Config.get("minecraft_dir")
        path = os.path.join(mc_dir, "instances")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @staticmethod
    def load_instances():
        if os.path.exists(InstanceManager.INSTANCES_FILE):
             try:
                 with open(InstanceManager.INSTANCES_FILE, "r") as f:
                     return json.load(f)
             except:
                 return {}
        return {}

    @staticmethod
    def save_instances(data):
        with open(InstanceManager.INSTANCES_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def create_instance(name, version, loader):
        instances = InstanceManager.load_instances()
        
        # Safe directory name
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
        instance_dir = os.path.join(InstanceManager.get_instances_dir(), safe_name)
        
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
            
        # Create standard folders
        os.makedirs(os.path.join(instance_dir, "mods"), exist_ok=True)
        os.makedirs(os.path.join(instance_dir, "resourcepacks"), exist_ok=True)
        os.makedirs(os.path.join(instance_dir, "shaderpacks"), exist_ok=True)
        
        instances[name] = {
            "name": name,
            "version": version,
            "loader": loader,
            "path": instance_dir
        }
        
        InstanceManager.save_instances(instances)
        return instances[name]

    @staticmethod
    def delete_instance(name):
        instances = InstanceManager.load_instances()
        if name in instances:
            data = instances[name]
            path = data["path"]
            
            # Remove Directory
            try:
                if os.path.exists(path):
                    shutil.rmtree(path)
            except Exception as e:
                print(f"Error deleting instance folder: {e}")
                
            # Remove from JSON
            del instances[name]
            InstanceManager.save_instances(instances)
            return True
        return False

    @staticmethod
    def get_instance(name):
        return InstanceManager.load_instances().get(name)
