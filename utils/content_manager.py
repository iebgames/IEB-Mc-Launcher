import os
import shutil
from .config import Config

class ContentManager:
    @staticmethod
    def get_dir(content_type, instance_path=None):
        if instance_path:
            base_dir = instance_path
        else:
            base_dir = Config.get("minecraft_dir")
            
        if content_type == "mod":
            return os.path.join(base_dir, "mods")
        elif content_type == "resourcepack":
            return os.path.join(base_dir, "resourcepacks")
        elif content_type == "shader":
            return os.path.join(base_dir, "shaderpacks")
        return None

    @staticmethod
    def list_content(content_type, instance_path=None):
        target_dir = ContentManager.get_dir(content_type, instance_path)
        if not target_dir or not os.path.exists(target_dir):
            return []
        
        files = []
        try:
            for f in os.listdir(target_dir):
                if f.endswith(".jar") or f.endswith(".zip"):
                    files.append(f)
        except Exception as e:
            print(f"Error listing {content_type}: {e}")
        return files

    @staticmethod
    def delete_content(content_type, filename, instance_path=None):
        target_dir = ContentManager.get_dir(content_type, instance_path)
        if not target_dir: return False
        
        path = os.path.join(target_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
                return True
        except Exception as e:
            print(f"Error deleting {filename}: {e}")
        return False
        
    @staticmethod
    def get_content_details(content_type, filename, instance_path=None):
        # Placeholder for metadata reading
        # Could read zip/jar manifest in future
        return {
            "name": filename,
            "path": os.path.join(ContentManager.get_dir(content_type, instance_path), filename)
        }
