#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

def clean():
    """Clean build artifacts."""
    print("Cleaning build directories...")
    dirs_to_clean = ['build', 'dist']
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Removed {d}/")

def install_deps():
    """Install required dependencies."""
    print("Installing requirements...")
    if os.path.exists("requirements.txt"):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            sys.exit(1)
    else:
        print("No requirements.txt found. Skipping.")

def run_tests():
    """Run unit tests."""
    print("Running tests...")
    # Example using unittest. Replace with pytest if needed.
    try:
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], check=False)
    except Exception as e:
        print(f"Could not execute tests: {e}")

def build():
    """Run the main build process (e.g., compiling, packaging)."""
    print("Starting build process...")
    # Add your project-specific build compilation or packaging tools here
    # Example: subprocess.run(["pyinstaller", "main.py"], check=True)
    os.makedirs('dist', exist_ok=True)
    print("Build complete. Artifacts placed in dist/")

def main():
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == "clean":
            clean()
        elif action == "test":
            run_tests()
        elif action == "deps":
            install_deps()
        else:
            print(f"Unknown action: {action}")
            print("Usage: python build.py [clean | test | deps]")
    else:
        # Default full build pipeline
        clean()
        install_deps()
        run_tests()
        build()

if __name__ == "__main__":
    main()
