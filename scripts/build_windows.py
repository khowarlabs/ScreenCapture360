import PyInstaller.__main__
import os
import sys

def build():
    # Define paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_path)
    main_script = os.path.join(project_root, "main.py")

    # PyInstaller arguments
    args = [
        main_script,
        "--name=Screen Recorder",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--version-file={os.path.join(base_path, 'file_version_info.txt')}",
        f"--workpath={os.path.join(project_root, 'build')}",
        f"--distpath={os.path.join(project_root, 'dist')}",
        "--hidden-import=PyQt6",
        "--hidden-import=mss",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=pygetwindow",
        "--hidden-import=av",
        "--hidden-import=sounddevice",
    ]

    print(f"Starting build for {main_script}...")
    PyInstaller.__main__.run(args)
    print("Build completed successfully!")

if __name__ == "__main__":
    build()
