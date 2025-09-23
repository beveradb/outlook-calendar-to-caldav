import subprocess
import time
import os
import objc
from AppKit import NSWorkspace


def launch_outlook() -> bool:
    """
    Launch the Outlook application on macOS, bringing it to the foreground.
    Returns:
        True if Outlook is running or launched successfully, False otherwise.
    """
    try:
        # Check if Outlook is already running
        running_apps = NSWorkspace.sharedWorkspace().runningApplications()
        for app in running_apps:
            if app.bundleIdentifier() == "com.microsoft.Outlook":
                print("Outlook is already running.")
                app.activateWithOptions_(0) # Bring to front
                return True

        # If not running, launch it
        print("Launching Outlook...")
        # Using osascript to launch to ensure it's a clean launch and in foreground
        script = 'tell application "Microsoft Outlook" to activate'
        subprocess.run(['osascript', '-e', script], check=True)
        time.sleep(5) # Give Outlook some time to launch

        # Verify it's running
        running_apps = NSWorkspace.sharedWorkspace().runningApplications()
        for app in running_apps:
            if app.bundleIdentifier() == "com.microsoft.Outlook":
                print("Outlook launched successfully.")
                return True
        print("Failed to launch Outlook.")
        return False
    except Exception as e:
        print(f"Error launching Outlook: {e}")
        return False


def navigate_to_calendar() -> bool:
    """
    Navigate to the calendar view in Outlook using CMD+2 shortcut.
    Returns:
        True if navigation is successful, False otherwise.
    Falls back to menu navigation if shortcut fails.
    """
    try:
        script = '''
        tell application "Microsoft Outlook"
            activate
            tell application "System Events"
                keystroke "2" using command down
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        time.sleep(2) # Give UI time to update
        print("Navigated to calendar successfully using CMD+2.")
        return True
    except Exception as e:
        print(f"Error navigating to calendar using CMD+2: {e}")
        # Fallback to menu item if shortcut fails
        print("Attempting to navigate via menu item: View -> Go To -> Calendar")
        try:
            script = '''
            tell application "Microsoft Outlook"
                activate
                tell application "System Events"
                    click menu item "Calendar" of menu "Go To" of menu "View" of menu bar 1
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            time.sleep(2) # Give UI time to update
            print("Navigated to calendar successfully via menu.")
            return True
        except Exception as menu_e:
            print(f"Error navigating to calendar via menu: {menu_e}")
            return False


def capture_screenshot(filepath: str) -> bool:
    """
    Capture a screenshot of the active window and save it to the specified filepath.
    Args:
        filepath: Path to save the screenshot
    Returns:
        True if screenshot is captured successfully, False otherwise.
    """
    try:
        # Use macOS's screencapture utility
        subprocess.run(["screencapture", "-o", "-x", filepath], check=True)
        print(f"Screenshot captured to {filepath}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error capturing screenshot: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during screenshot capture: {e}")
        return False
