"""
WLED Matrix Fade Effect - Pyscript Version for Home Assistant
Requires: Pyscript integration (install via HACS)
"""

import requests
import time
import random
import math
import asyncio

# Configuration (you can also set these via Home Assistant input_number helpers)
WLED_IP = "10.0.42.15"
WLED_URL = f"http://{WLED_IP}/json/state"
SEGMENT_ID = 1

# Matrix coordinates
START_X = 0
STOP_X = 4
START_Y = 80
STOP_Y = 139

# Effect parameters
NUM_SEGMENTS_MIN = 3
NUM_SEGMENTS_MAX = 6
SEGMENT_LENGTH_MIN = 3
SEGMENT_LENGTH_MAX = 5
FADE_IN_SECONDS = 20
STAY_ON_MIN = 30
STAY_ON_MAX = 60
FADE_OUT_SECONDS = 20
FADE_STEPS_PER_SECOND = 5
LED_BRIGHTNESS = 255
MIN_SPACING = 1

# Global state
active_segments = {}
running = False
segment_counter = 0


def calculate_led_index(x, y):
    """Calculate LED index for given x, y position"""
    width = STOP_X - START_X + 1
    adj_y = y - START_Y
    adj_x = x - START_X

    if adj_y % 2 == 0:
        led_index = adj_y * width + adj_x
    else:
        led_index = adj_y * width + (width - 1 - adj_x)

    return led_index


def ease_in_out(t):
    """Smooth easing function"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - math.pow(-2 * t + 2, 3) / 2


def check_overlap(start_y, end_y):
    """Check if a Y range overlaps with any active segments"""
    for seg_id, (seg_start, seg_end) in active_segments.items():
        if not (end_y + MIN_SPACING < seg_start or start_y > seg_end + MIN_SPACING):
            return True
    return False


@service
def wled_fade_start():
    """Start the WLED fade effect"""
    global running, segment_counter, active_segments

    if running:
        log.warning("WLED fade effect is already running")
        return

    running = True
    active_segments = {}
    segment_counter = 0

    # Clear segment
    blackout_segment()

    # Start effect task
    task.unique("wled_fade_effect")
    run_effect()

    log.info("WLED fade effect started")


@service
def wled_fade_stop():
    """Stop the WLED fade effect"""
    global running

    running = False
    task.unique("wled_fade_effect", kill_me=True)

    log.info("WLED fade effect stopped")


def blackout_segment():
    """Clear all LEDs"""
    height = STOP_Y - START_Y + 1
    width = STOP_X - START_X + 1
    total_leds = height * width

    led_array = []
    for i in range(total_leds):
        led_array.extend([i, "000000"])

    payload = {"seg": {"id": SEGMENT_ID, "i": led_array}}

    try:
        requests.post(WLED_URL, json=payload, timeout=2)
        time.sleep(0.2)

        payload2 = {
            "seg": {
                "id": SEGMENT_ID,
                "i": [],
                "col": [[0, 0, 0]],
                "bri": 255,
                "on": True,
            }
        }
        requests.post(WLED_URL, json=payload2, timeout=2)
        time.sleep(0.5)
    except Exception as e:
        log.error(f"Error during blackout: {e}")


@task_unique("wled_fade_segment_{segment_id}")
async def fade_segment_lifecycle(segment_id):
    """Run one complete lifecycle for a single segment"""
    global running, active_segments, segment_counter

    # Random delay before starting
    await asyncio.sleep(random.uniform(0, 3))

    if not running:
        return

    # Choose random position
    segment_length = random.randint(SEGMENT_LENGTH_MIN, SEGMENT_LENGTH_MAX)
    max_start_y = STOP_Y - segment_length + 1

    # Try to find non-overlapping position
    start_y = None
    for attempt in range(20):
        candidate_start = random.randint(START_Y, max_start_y)
        candidate_end = candidate_start + segment_length - 1

        if not check_overlap(candidate_start, candidate_end):
            start_y = candidate_start
            break

    if start_y is None:
        log.debug(f"Segment {segment_id} skipped - no space available")
        # Spawn replacement
        segment_counter += 1
        fade_segment_lifecycle(segment_counter)
        return

    # Register segment
    end_y = start_y + segment_length - 1
    active_segments[segment_id] = (start_y, end_y)

    # Create LED list
    led_indices = []
    for y in range(start_y, start_y + segment_length):
        for x in range(START_X, STOP_X + 1):
            led_indices.append(calculate_led_index(x, y))

    log.info(f"Segment {segment_id}: Y rows {start_y}-{end_y} ({segment_length} rows, {len(led_indices)} LEDs)")

    # FADE IN
    num_steps = int(FADE_IN_SECONDS * FADE_STEPS_PER_SECOND)
    step_duration = FADE_IN_SECONDS / num_steps

    for step in range(num_steps + 1):
        if not running:
            return

        progress = step / num_steps
        brightness = int(LED_BRIGHTNESS * ease_in_out(progress))

        led_array = []
        hex_color = f"{brightness:02x}{brightness:02x}{brightness:02x}"
        for led_index in led_indices:
            led_array.extend([led_index, hex_color])

        payload = {"seg": {"id": SEGMENT_ID, "i": led_array, "bri": 255}}
        try:
            requests.post(WLED_URL, json=payload, timeout=1)
        except:
            pass

        await asyncio.sleep(step_duration)

    if not running:
        return

    # STAY ON
    stay_duration = random.uniform(STAY_ON_MIN, STAY_ON_MAX)
    await asyncio.sleep(stay_duration)

    if not running:
        return

    # Unregister and spawn replacement
    active_segments.pop(segment_id, None)
    segment_counter += 1
    fade_segment_lifecycle(segment_counter)

    # FADE OUT
    num_steps = int(FADE_OUT_SECONDS * FADE_STEPS_PER_SECOND)
    step_duration = FADE_OUT_SECONDS / num_steps

    for step in range(num_steps + 1):
        if not running:
            return

        progress = step / num_steps
        brightness = int(LED_BRIGHTNESS * ease_in_out(1.0 - progress))

        led_array = []
        hex_color = f"{brightness:02x}{brightness:02x}{brightness:02x}"
        for led_index in led_indices:
            led_array.extend([led_index, hex_color])

        payload = {"seg": {"id": SEGMENT_ID, "i": led_array, "bri": 255}}
        try:
            requests.post(WLED_URL, json=payload, timeout=1)
        except:
            pass

        await asyncio.sleep(step_duration)

    # Clear LEDs
    led_array = []
    for led_index in led_indices:
        led_array.extend([led_index, "000000"])

    payload = {"seg": {"id": SEGMENT_ID, "i": led_array, "bri": 255}}
    try:
        requests.post(WLED_URL, json=payload, timeout=1)
    except:
        pass


@task_unique("wled_fade_effect")
async def run_effect():
    """Main effect loop"""
    global segment_counter

    target_segments = random.randint(NUM_SEGMENTS_MIN, NUM_SEGMENTS_MAX)

    # Start initial segments
    for i in range(target_segments):
        segment_counter += 1
        fade_segment_lifecycle(segment_counter)
        await asyncio.sleep(random.uniform(0.5, 1.5))

    # Keep running
    while running:
        await asyncio.sleep(10)
