import shutil
import os
import tkinter as tk
from tkinter import filedialog
from .config import Config

class FileInstaller:
    @staticmethod
    def install_mod(target_dir=None):
        if not target_dir:
            # Default to <minecraft_dir>/mods
            mc_dir = Config.get("minecraft_dir")
            target_dir = os.path.join(mc_dir, "mods")
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        files = filedialog.askopenfilenames(
            title="Select Mods",
            filetypes=[("Jar Files", "*.jar"), ("Zip Files", "*.zip")]
        )
        
        if not files:
            return 0

        count = 0
        for file in files:
            try:
                shutil.copy(file, target_dir)
                count += 1
            except Exception as e:
                print(f"Error copying {file}: {e}")
        
        return count

    @staticmethod
    def install_resource_pack():
        mc_dir = Config.get("minecraft_dir")
        target_dir = os.path.join(mc_dir, "resourcepacks")
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        files = filedialog.askopenfilenames(
            title="Select Resource Packs",
            filetypes=[("Zip Files", "*.zip")]
        )
        
        if not files:
            return 0

        count = 0
        for file in files:
            try:
                shutil.copy(file, target_dir)
                count += 1
            except Exception as e:
                print(f"Error copying {file}: {e}")
        
        return count
    
    @staticmethod
    def install_shader_pack():
        mc_dir = Config.get("minecraft_dir")
        target_dir = os.path.join(mc_dir, "shaderpacks")
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        files = filedialog.askopenfilenames(
            title="Select Shader Packs",
            filetypes=[("Zip Files", "*.zip")]
        )
        
        if not files:
            return 0

        count = 0
        for file in files:
            try:
                shutil.copy(file, target_dir)
                count += 1
            except Exception as e:
                print(f"Error copying {file}: {e}")
        
        return count
