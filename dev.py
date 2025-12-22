import os
import subprocess
import sys
import time
import warnings

# Suppress Pydantic V2 warnings from dependencies
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")
# Suppress Pydub warnings about ffmpeg
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv")

os.environ["OPENMANUS_NON_INTERACTIVE"] = "true"


def run_backend():

    print("🚀 Starting Backend API Server...")
    return subprocess.Popen([sys.executable, "-m", "app.api.server"], env=os.environ)


def run_frontend():
    print("🎨 Starting Frontend Dev Server...")
    # Using npm run dev, assuming dependencies are installed
    return subprocess.Popen(["npm", "run", "dev"], cwd="frontend", shell=True)


def main():
    backend_proc = None
    frontend_proc = None
    try:
        backend_proc = run_backend()
        time.sleep(2)  # Give backend time to start
        frontend_proc = run_frontend()

        print("\n✅ OpenManus is running!")
        print("🔗 API: http://localhost:8000")
        print("🔗 Web UI: http://localhost:3000\n")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping OpenManus...")
    finally:
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()


if __name__ == "__main__":
    main()
