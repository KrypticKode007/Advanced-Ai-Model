#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

def clean():
    """Clean build artifacts."""
    print("Cleaning build directories...")
    dirs_to_clean = [ROOT / 'build', ROOT / 'dist']
    for d in dirs_to_clean:
        if d.exists():
            shutil.rmtree(d)
            print(f"Removed {d}/")

def install_deps():
    """Install required dependencies."""
    print("Installing requirements...")
    requirements = ROOT / "requirements.txt"
    if requirements.exists():
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements)],
                check=True,
                cwd=ROOT,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            sys.exit(1)
    else:
        print("No requirements.txt found. Skipping.")

def run_tests():
    """Run the project's pytest suite and fail the build on test errors."""
    print("Running pytest...")
    subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True, cwd=ROOT)

def build():
    """Run the main build process (e.g., compiling, packaging)."""
    print("Starting build process...")
    # Add your project-specific build compilation or packaging tools here
    # Example: subprocess.run(["pyinstaller", "main.py"], check=True)
    (ROOT / 'dist').mkdir(exist_ok=True)
    print(f"Build complete. Artifacts placed in {ROOT / 'dist'}/")

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
