import os
import glob
import re
import requests
import time

# System tray icon imports
import threading
import pystray
from PIL import Image, ImageDraw


# Map Teams status to colors
STATUS_COLORS = {
    'Available': (0, 200, 0),      # Green
    'Busy': (255, 0, 0),          # Red
    'DoNotDisturb': (255, 0, 0),  # Red
    'Away': (255, 200, 0),        # Yellow
    'BeRightBack': (255, 200, 0), # Yellow
    'Offline': (128, 128, 128),   # Gray
    'OnThePhone': (0, 128, 255),  # Blue
    'Presenting': (128, 0, 255),  # Purple
}

def create_image(status=None):
    color = STATUS_COLORS.get(status, (0, 128, 255))
    image = Image.new('RGB', (16, 16), color)
    d = ImageDraw.Draw(image)
    d.rectangle([4, 4, 12, 12], fill=(255, 255, 255))
    return image


# Tray icon menu actions
def on_quit(icon, item):
    icon.stop()
    os._exit(0)

def on_show_log(icon, item):
    # Open the latest log file in Notepad
    log_file = find_latest_log(LOG_DIR)
    if log_file:
        os.system(f'start notepad.exe "{log_file}"')
    else:
        # Optionally, show a message box if no log is found
        pass

# Tray icon thread function

# Global reference to tray icon for updates
tray_icon_ref = None

def tray_icon():
    global tray_icon_ref
    icon = pystray.Icon(
        "TeamsStatus",
        create_image(),
        "Teams Status",
        menu=pystray.Menu(
            pystray.MenuItem("Show Log", on_show_log),
            pystray.MenuItem("Quit", on_quit)
        )
    )
    tray_icon_ref = icon
    icon.run()

LOG_DIR = r"C:\Users\USER\AppData\Local\Packages\MSTeams_8wekyb3d8bbwe\LocalCache\Microsoft\MSTeams\Logs"
STATUS_REGEX = r'status (\w+)'
ESP_ADDRESS = "http://192.168.10.111/?status="  # Replace <PI_IP> with your Pi's IP

def find_latest_log(log_dir):
    files = glob.glob(os.path.join(log_dir, "MSTeams_*.log"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def get_latest_status(log_file):
    latest_status = None
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = re.search(STATUS_REGEX, line)
            if match:
                latest_status = match.group(1)
    return latest_status

def send_status_to_pi(status):
    try:
        requests.get(ESP_ADDRESS + status)
        print(f"Sent status '{status}' to ESP32 via query string.")
    except Exception as e:
        print(f"Failed to send status: {e}")


def main():
    global tray_icon_ref
    last_status = None
    last_log_file = None
    last_position = 0
    while True:
        log_file = find_latest_log(LOG_DIR)
        if not log_file:
            print("No log file found.")
            time.sleep(1)
            continue

        # If the log file changed (new file), reset position
        if log_file != last_log_file:
            last_log_file = log_file
            last_position = 0

        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()
        except Exception as e:
            print(f"Error reading log: {e}")
            time.sleep(1)
            continue

        for line in new_lines:
            match = re.search(STATUS_REGEX, line)
            if match:
                status = match.group(1)
                if status != last_status:
                    send_status_to_pi(status)
                    last_status = status
                    print(f"Detected new status: {status}")
                    # Update tray icon color
                    if tray_icon_ref:
                        tray_icon_ref.icon = create_image(status)
        time.sleep(1)  # Check every 10 seconds

if __name__ == "__main__":
    # Start tray icon in a separate thread
    threading.Thread(target=tray_icon, daemon=True).start()
    main()