import os
import glob
import shutil


def clean():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("APPDATA not set")
        return

    base = os.path.join(appdata, "Code", "User", "globalStorage")
    pattern = os.path.join(base, "github.copilot*")

    print(f"Looking for {pattern}")
    found = glob.glob(pattern)

    if not found:
        print("No cache folders found")
        return

    for path in found:
        print(f"Removing {path}")
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print("Success")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    clean()
