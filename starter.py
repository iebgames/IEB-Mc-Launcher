import os
import sys
import subprocess
import pkg_resources

def check_dependencies():
    required = set()
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                required.add(line)

    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed

    if missing:
        print(f"Missing dependencies: {missing}")
        print("Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError:
            print("Failed to install dependencies.")
            sys.exit(1)
    else:
        print("All dependencies are satisfied.")

def launch_main():
    print("Launching IEB-MC-Launcher...")
    try:
        subprocess.call([sys.executable, 'main.py'])
    except Exception as e:
        print(f"Failed to launch main.py: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    # Ensure we are in the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    check_dependencies()
    launch_main()
