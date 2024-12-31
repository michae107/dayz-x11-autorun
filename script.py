#!/usr/bin/env python3
import subprocess
import time
from Xlib import X, display
from Xlib.ext import record
from Xlib.protocol import rq
from Xlib.display import Display

# 1. Configure which application you want to track
TARGET_WINDOW_NAME = "DayZ"   # e.g., the title shown in the window bar

# 2. Global or “sticky” variables
sticky_mode = False
key_states = {
    "W": False,
    "A": False,
    "S": False,
    "D": False,
    "Shift": False
}

# 3. Utility to check current active window name
def get_active_window_name():
    try:
        # Using xdotool for simplicity
        window_id = subprocess.check_output(["xdotool", "getactivewindow"]).strip()
        window_name = subprocess.check_output(["xdotool", "getwindowname", window_id]).decode("utf-8").strip()
        return window_name
    except subprocess.CalledProcessError:
        return None

# 4. Utility to simulate key press/release
def send_key_event(key, press=True):
    """
    Use xdotool to simulate a keypress or keyrelease.
    """
    action = "keydown" if press else "keyup"
    subprocess.run(["xdotool", action, key])

# 5. Handler for our key events
def process_key_event(event):
    global sticky_mode, key_states

    # We only want to do something special if the target app is in focus
    current_window = get_active_window_name()
    if current_window != TARGET_WINDOW_NAME:
        for k, is_stuck in key_states.items():
            if is_stuck:
                send_key_event(k, press=False)
                print("window change unstick " + k)
        return  # do nothing

    # Convert X keycode to a string (“W”, “A”, etc.) - we have to map them properly
    keycode = event.detail
    state = event.type  # KeyPress or KeyRelease
    is_press = (state == X.KeyRelease)
    print(keycode)

    # Minimal keycode -> char mapping snippet (adjust as needed!)
    # You’ll need the real mappings for your system.
    KEYCODE_TO_CHAR = {
        25: "W",   # This is just an example. Use xev to find actual keycodes
        38: "A",
        39: "S",
        40: "D",
        50: "Shift",
        28: "T",
        24: "Q"
    }

    char = KEYCODE_TO_CHAR.get(keycode, None)
    if not char:
        return

    if char == "Q" and is_press:
        sticky_mode = not sticky_mode
        print(f"[INFO] Q was pressed. Sticky Mode = {sticky_mode}")
        for k, is_stuck in key_states.items():
            if is_stuck:
                send_key_event(k, press=False)
                print("unstick " + char)
        key_states = {k: False for k in key_states}
        return

    if not char in ('W', 'Shift'):
        print("ignore char " + char)
        return

    if sticky_mode and is_press and char in key_states:
        print("stick " + char)
        send_key_event(char, press=False)
        send_key_event(char, press=True)
        key_states[char] = True

def main():
    # Create our display & record context
    local_dpy = display.Display()
    record_dpy = display.Display()

    def callback(reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print("Byte-swapped protocols not supported.")
            return
        if len(reply.data) < 2:
            return

        # Extract events
        events = reply.data
        i = 0
        while i < len(events):
            event, _ = rq.EventField(None).parse_binary_value(
                events, record_dpy.display, None, None
            )
            if event.type in [X.KeyPress, X.KeyRelease]:
                process_key_event(event)
            i += 32  # next event

    # Record key press/release at the X level
    ctx = record_dpy.record_create_context(
        0,
        [record.AllClients],
        [
            {
                "core_requests": (0, 0),
                "core_replies": (0, 0),
                "ext_requests": (0, 0, 0, 0),
                "ext_replies": (0, 0, 0, 0),
                "delivered_events": (X.KeyPress, X.MotionNotify),
                "device_events": (0, 0),
                "errors": (0, 0),
                "client_started": False,
                "client_died": False,
            }
        ],
    )

    # Enable the record context and run indefinitely
    record_dpy.record_enable_context(ctx, callback)
    record_dpy.record_free_context(ctx)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
