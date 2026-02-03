import minecraft_launcher_lib
import subprocess
import os
import uuid
import platform
import requests
from utils.config import Config

# --- Monkeypatch for minecraft-launcher-lib crash (ValueError: too many values to unpack) ---
from minecraft_launcher_lib.helper import parse_rule_list
from minecraft_launcher_lib.natives import get_natives

def patched_get_libraries(data, path):
    if platform.system() == "Windows":
        classpath_seperator = ";"
    else:
        classpath_seperator = ":"
    libstr = ""
    for i in data["libraries"]:
        if not parse_rule_list(i, "rules", {}):
            continue
        current_path = os.path.join(path, "libraries")
        
        # PATCH: Robust split for names with classifiers (e.g. group:name:ver:classifier)
        parts = i["name"].split(":")
        lib_path, name, version = parts[0], parts[1], parts[2]
        
        for lib_part in lib_path.split("."):
            current_path = os.path.join(current_path, lib_part)
        current_path = os.path.join(current_path, name, version)
        native = get_natives(i)
        if native == "":
            jar_filename = name + "-" + version + ".jar"
        else:
            jar_filename = name + "-" + version + "-" + native + ".jar"
        current_path = os.path.join(current_path, jar_filename)
        libstr = libstr + current_path + classpath_seperator
    if "jar" in data:
        libstr = libstr + os.path.join(path, "versions", data["jar"], data["jar"] + ".jar")
    else:
        libstr = libstr + os.path.join(path, "versions", data["id"], data["id"] + ".jar")
    return libstr

# Apply Patch
minecraft_launcher_lib.command.get_libraries = patched_get_libraries
# -------------------------------------------------------------------------------------------

class LauncherCore:
    def __init__(self):
        raw_dir = Config.get("minecraft_dir")
        # Ensure dir exists first
        if not os.path.exists(raw_dir):
             try:
                 os.makedirs(raw_dir)
             except Exception as e:
                 print(f"Error creating minecraft directory: {e}")
        
        # Convert to Short Path (Windows 8.3) to avoid encoding issues with Java
        self.minecraft_dir = self._get_short_path(raw_dir)
        print(f"Using Minecraft Dir: {self.minecraft_dir}")

    def _get_short_path(self, path):
        if os.name == 'nt':
            try:
                import ctypes
                buffer_size = 1024
                buffer = ctypes.create_unicode_buffer(buffer_size)
                # GetShortPathNameW handles unicode input and returns short path
                l = ctypes.windll.kernel32.GetShortPathNameW(path, buffer, buffer_size)
                if l > 0:
                    return buffer.value
            except Exception as e:
                print(f"Short Path Error: {e}")
        return path

    def get_installed_versions(self):
        return minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_dir)

    def get_available_versions(self):
        # Returns a list of versions from Mojang
        return minecraft_launcher_lib.utils.get_available_versions(self.minecraft_dir)

    def install_version(self, version_id, callback=None):
        minecraft_launcher_lib.install.install_minecraft_version(
            versionid=version_id,
            minecraft_directory=self.minecraft_dir,
            callback=callback
        )

    def install_and_get_version(self, vanilla_version, loader_type, callback=None, game_dir=None):
        """
        Installs vanilla version if needed, then installs the requested loader 
        and returns the resulting version ID to launch.
        """
        # Determine target directory
        target_dir = game_dir if game_dir else self.minecraft_dir
        
        # Always ensure vanilla is installed first (Usually vanilla needs to be in main dir for some loaders to find it? 
        # Actually minecraft-launcher-lib handles inheritance.
        # But for full isolation, we might want it in instance dir? 
        # Usually it's better to keep versions in main dir and only run game in instance dir (gameDirectory option).
        # WAITING: install_minecraft_version installs ASSETS and LIBRARIES. These are shared.
        # So install_minecraft_version should probably ALWAYS target self.minecraft_dir (shared cache).
        # But mod loaders create a new VERSION JSON.
        
        # Strategy:
        # 1. Install Vanilla -> Shared Dir (self.minecraft_dir)
        # 2. Install Loader -> Shared Dir (self.minecraft_dir) [Versions are shared]
        # 3. Launch Game -> options["gameDirectory"] = game_dir [Mods/Configs isolated]
        
        self.install_version(vanilla_version, callback)
        
        if loader_type == "None":
            return vanilla_version
            
        elif loader_type == "Forge":
            # Check if already installed?
            # Ideally find installed forge version matching vanilla
            # For simplicity, we run installer. 
            # minecraft-launcher-lib has install_forge_version(versionid, path)
            # which automatically finds latest forge for that version.
            print(f"Installing Forge for {vanilla_version}...")
            minecraft_launcher_lib.forge.install_forge_version(vanilla_version, self.minecraft_dir, callback=callback)
            
            # Find the ID of the installed forge version
            # Usually generic convention or we need to search 'versions' folder
            installed = self.get_installed_versions()
            for v in installed:
                if v["id"].startswith(f"{vanilla_version}-forge"):
                    return v["id"]
            # Fallback if naming is different (older forge)
            # Try to find one containing both
            for v in installed:
                if vanilla_version in v["id"] and "forge" in v["id"].lower():
                    return v["id"]
                    
        elif loader_type == "Fabric":
            print(f"Installing Fabric for {vanilla_version}...")
            minecraft_launcher_lib.fabric.install_fabric(vanilla_version, self.minecraft_dir, callback=callback)
            
            # Find ID
            installed = self.get_installed_versions()
            for v in installed:
                if "fabric" in v["id"].lower() and vanilla_version in v["id"]:
                    return v["id"]

        elif loader_type == "Quilt":
            print(f"Installing Quilt for {vanilla_version}...")
            minecraft_launcher_lib.quilt.install_quilt(vanilla_version, self.minecraft_dir, callback=callback)
            
            installed = self.get_installed_versions()
            for v in installed:
                if "quilt" in v["id"].lower() and vanilla_version in v["id"]:
                    return v["id"]
        
        # OptiFine
        # Mod Loaders that require manual jar running (OptiFine) are harder to automate 
        # via minecraft-launcher-lib directly unless it supports it.
        # Assuming manual install or unsupported for now, fallback to vanilla
        print(f"Loader {loader_type} automation not fully supported yet, returning vanilla.")
        return vanilla_version

    def launch_game(self, version_id, username, profile_type="offline", game_dir=None, access_token=None): 
        # Java Path Logic
        java_path = Config.get("java_path", "java")
        final_java_path = None
        
        if java_path != "java" and java_path:
             # User specified strict path
             final_java_path = java_path
             print(f"Using user-specified Java: {java_path}")
        else:
             # Default: Try to use bundled runtime first
             try:
                 vdata = minecraft_launcher_lib.utils.get_version_data(version_id, self.minecraft_dir)
                 if "javaVersion" in vdata:
                     component = vdata["javaVersion"]["component"]
                     major_version = vdata["javaVersion"]["majorVersion"]
                     
                     # Check if runtime exists, if not install it
                     from minecraft_launcher_lib.runtime import get_jvm_runtimes
                     runtimes = get_jvm_runtimes()
                     
                     # Check if we have this runtime installed
                     runtime_path = os.path.join(self.minecraft_dir, "runtime", component)
                     if not os.path.exists(runtime_path):
                         print(f"Installing Java {major_version} runtime...")
                         try:
                             from minecraft_launcher_lib.runtime import install_jvm_runtime
                             install_jvm_runtime(component, self.minecraft_dir, callback={
                                 "setStatus": lambda x: print(f"Runtime: {x}"),
                                 "setProgress": lambda x: None,
                                 "setMax": lambda x: None
                             })
                             print(f"Java {major_version} runtime installed successfully")
                         except Exception as e:
                             print(f"Failed to install runtime: {e}")
                             final_java_path = self._autodetect_java()
                     
                     # DON'T set final_java_path - let library use bundled runtime
                     print(f"Will use bundled Java {major_version} runtime")
                 else:
                     # No java version specified (old versions), use auto-detect
                     final_java_path = self._autodetect_java()
                     print(f"Legacy version, using auto-detected Java")
             except Exception as e:
                 print(f"Error checking version data: {e}")
                 final_java_path = self._autodetect_java()

        # Default options
        options = {
            "username": username,
            "uuid": str(uuid.uuid4()),
            "token": access_token if access_token else "",
            "jvmArguments": self._get_jvm_args()
        }
        
        if final_java_path:
            options["executablePath"] = final_java_path
            print(f"Using Java Path: {final_java_path}")
        else:
            print("Using Bundled Java Runtime (managed by library)")
        
        if game_dir:
            options["gameDirectory"] = game_dir
        
        # Ely.by Support
        if profile_type == "elyby":
             authlib_path = self._check_authlib()
             if authlib_path:
                 # Add javaagent to JVM args
                 auth_arg = f"-javaagent:{authlib_path}=ely.by"
                 options["jvmArguments"].append(auth_arg)
                 print(f"Injecting Ely.by authlib with token: {access_token[:20] if access_token else 'None'}...")
             else:
                 print("Warning: Ely.by selected but authlib-injector could not be found/downloaded!")

        command = minecraft_launcher_lib.command.get_minecraft_command(
            version=version_id,
            minecraft_directory=self.minecraft_dir,
            options=options
        )
        
        print(f"Launching command: {' '.join(command[:5])}...")  # Print first few args for debugging
        
        # Launch with output capture
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Start thread to monitor output
            import threading
            def monitor_output():
                try:
                    for line in process.stdout:
                        print(f"[GAME] {line.strip()}")
                    for line in process.stderr:
                        print(f"[GAME ERROR] {line.strip()}")
                except Exception as e:
                    print(f"Error monitoring game output: {e}")
            
            threading.Thread(target=monitor_output, daemon=True).start()
            
            # Check if process started successfully
            import time
            time.sleep(1)
            if process.poll() is not None:
                # Process already exited
                stdout, stderr = process.communicate()
                print(f"Game crashed immediately!")
                print(f"Exit code: {process.returncode}")
                if stdout:
                    print(f"STDOUT:\n{stdout}")
                if stderr:
                    print(f"STDERR:\n{stderr}")
            else:
                print("Game process started successfully")
                
        except Exception as e:
            print(f"Failed to launch game: {e}")
            import traceback
            traceback.print_exc()

    def _check_authlib(self):
        """Checks for authlib-injector, downloads if missing."""
        lib_dir = os.path.join(os.getcwd(), "authlib")
        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)
            
        jar_path = os.path.join(lib_dir, "authlib-injector.jar")
        
        if not os.path.exists(jar_path):
            print("Downloading authlib-injector...")
            try:
                # Using latest release from yushijinhun's authlib-injector
                # Direct link to stable version (e.g. 1.2.5) or latest
                url = "https://github.com/yushijinhun/authlib-injector/releases/download/v1.2.5/authlib-injector-1.2.5.jar"
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(jar_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print("Authlib-injector downloaded.")
                    return jar_path
                else:
                    print(f"Failed to download authlib: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Error downloading authlib: {e}")
                return None
        return jar_path

    def _autodetect_java(self):
        # 1. Check JAVA_HOME
        jh = os.environ.get("JAVA_HOME")
        if jh:
            bin_java = os.path.join(jh, "bin", "javaw.exe" if os.name == 'nt' else "java")
            if os.path.exists(bin_java): return bin_java
            
        # 2. Scan Common Windows Paths
        if os.name == 'nt':
            search_paths = [
                r"C:\Program Files\Java",
                r"C:\Program Files (x86)\Java",
                r"C:\Program Files\Eclipse Adoptium",
                r"C:\Users\Public\Java"
            ]
            
            candidates = []
            for path in search_paths:
                if os.path.exists(path):
                    try:
                        for entry in os.scandir(path):
                            if entry.is_dir() and (entry.name.startswith("jdk") or entry.name.startswith("jre")):
                                jpath = os.path.join(entry.path, "bin", "javaw.exe")
                                if os.path.exists(jpath):
                                    candidates.append(jpath)
                    except: pass
            
            # Smart Selection: Prefer JDK over JRE, Newer versions (lexicographically roughly works for jdk-17 vs jdk-1.8)
            if candidates:
                candidates.sort(reverse=True) # Sort to get likely newer versions first (e.g. jdk-17 > jdk-11)
                return candidates[0]
                
        # 3. Path fallback
        import shutil
        return shutil.which("javaw") or shutil.which("java")

    def _get_jvm_args(self):
        ram = int(Config.get("ram", 2048))
        fps_boost = Config.get("fps_boost", False)
        
        # Base RAM args
        # Note: minecraft-launcher-lib handles Xmx/Xms via 'jvmArguments' if passed as list? 
        # Actually get_minecraft_command usually handles RAM if passed in options specifically?
        # Checking docs/usage: typically one passes "jvmArguments": ["-Xmx2G", ...]
        
        args = [f"-Xmx{ram}M", "-Xms128M"]
        
        if fps_boost:
            try:
                cpu_count = os.cpu_count() or 4
                args.extend([
                    "-XX:+UnlockExperimentalVMOptions",
                    f"-XX:ParallelGCThreads={cpu_count * 2}",
                    "-XX:+AggressiveOpts",
                    "-XX:+AggressiveHeap"
                ])
            except:
                pass
                
        return args
