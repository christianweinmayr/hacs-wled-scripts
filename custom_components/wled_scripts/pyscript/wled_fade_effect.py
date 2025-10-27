"""
WLED Matrix Fade Effect - Pyscript Version for Home Assistant
Requires: Pyscript integration (install via HACS)
"""

import random
import math

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

# Global state - use regular Python variables (pyscript.* state vars have type issues)
active_segments = {}
running = False
segment_counter = 0
active_tasks = set()  # Track all active segment task names


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


async def interruptible_sleep(duration):
    """Sleep in small chunks so we can exit quickly if stopped"""
    remaining_time = duration
    while remaining_time > 0 and running:
        sleep_time = min(0.5, remaining_time)  # Check every 0.5 seconds
        await task.sleep(sleep_time)
        remaining_time -= sleep_time
    return running  # Return False if interrupted


def check_overlap(start_y, end_y):
    """Check if a Y range overlaps with any active segments"""
    for seg_id, (seg_start, seg_end) in active_segments.items():
        if not (end_y + MIN_SPACING < seg_start or start_y > seg_end + MIN_SPACING):
            return True
    return False


async def send_wled_command_async(payload):
    """Send command to WLED using REST API"""
    import aiohttp
    try:
        log.debug(f"Sending to {WLED_URL}: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post(WLED_URL, json=payload, timeout=aiohttp.ClientTimeout(total=2)) as resp:
                if resp.status == 200:
                    log.debug(f"WLED command successful")
                else:
                    log.error(f"WLED returned status {resp.status}")
                    response_text = await resp.text()
                    log.error(f"Response: {response_text}")
    except Exception as e:
        log.error(f"Error sending WLED command to {WLED_URL}: {e}")
        import traceback
        log.error(f"Traceback: {traceback.format_exc()}")


async def _do_stop():
    """Internal helper to stop the effect"""
    global running, active_tasks

    log.info(f"Stopping WLED fade effect - killing {len(active_tasks)} segment tasks")

    running = False

    # Kill main effect task
    task.unique("wled_fade_effect", kill_me=True)

    # Kill all active segment tasks
    for task_name in list(active_tasks):
        log.debug(f"Killing task: {task_name}")
        task.unique(task_name, kill_me=True)

    active_tasks.clear()

    # Clear all LEDs immediately
    await blackout_segment()

    log.info("WLED fade effect stopped")


@service
async def wled_fade_start():
    """Start the WLED fade effect"""
    global running, active_segments, segment_counter, active_tasks

    log.info(f"wled_fade_start called - current running state: {running}")

    if running:
        log.warning("WLED fade effect is already running - stopping it first")
        await _do_stop()
        await task.sleep(1)

    log.info(f"Starting WLED fade effect - IP: {WLED_IP}, Segment: {SEGMENT_ID}")
    log.info(f"Matrix: X({START_X}-{STOP_X}), Y({START_Y}-{STOP_Y})")

    running = True
    active_segments = {}
    segment_counter = 0
    active_tasks = set()

    # Clear segment
    log.info("Clearing WLED segment...")
    await blackout_segment()
    log.info("Blackout complete")

    # Start effect task
    log.info("Creating run_effect task...")
    task.unique("wled_fade_effect")
    run_effect()

    log.info("WLED fade effect started - check logs for 'Segment X:' messages")


@service
async def wled_fade_stop():
    """Stop the WLED fade effect"""
    await _do_stop()


async def blackout_segment():
    """Clear all LEDs"""
    height = STOP_Y - START_Y + 1
    width = STOP_X - START_X + 1
    total_leds = height * width

    led_array = []
    for i in range(total_leds):
        led_array.extend([i, "000000"])

    payload = {"seg": {"id": SEGMENT_ID, "i": led_array}}

    await send_wled_command_async(payload)
    await task.sleep(0.2)

    payload2 = {
        "seg": {
            "id": SEGMENT_ID,
            "i": [],
            "col": [[0, 0, 0]],
            "bri": 255,
            "on": True,
        }
    }
    await send_wled_command_async(payload2)
    await task.sleep(0.5)


async def fade_segment_lifecycle(segment_id):
    """Run one complete lifecycle for a single segment"""
    global running, active_segments, segment_counter, active_tasks

    task_name = f"segment_{segment_id}"

    # Random delay before starting
    if not await interruptible_sleep(random.uniform(0, 3)):
        active_tasks.discard(task_name)
        return

    if not running:
        active_tasks.discard(task_name)
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
        active_tasks.discard(task_name)
        # Don't spawn replacement - just exit. Main loop will handle spawning new segments
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
            active_tasks.discard(task_name)
            return

        progress = step / num_steps
        brightness = int(LED_BRIGHTNESS * ease_in_out(progress))

        led_array = []
        hex_color = f"{brightness:02x}{brightness:02x}{brightness:02x}"
        for led_index in led_indices:
            led_array.extend([led_index, hex_color])

        payload = {"seg": {"id": SEGMENT_ID, "i": led_array, "bri": 255}}
        await send_wled_command_async(payload)

        await task.sleep(step_duration)

    if not running:
        active_tasks.discard(task_name)
        return

    # STAY ON
    stay_duration = random.uniform(STAY_ON_MIN, STAY_ON_MAX)

    # Spawn replacement during stay-on phase (before fade-out) to maintain continuous lighting
    # Wait for most of the stay duration, then spawn new segment
    spawn_delay = max(stay_duration - FADE_IN_SECONDS, stay_duration * 0.5)
    if not await interruptible_sleep(spawn_delay):
        active_tasks.discard(task_name)
        return

    # Spawn replacement now (while we're still fully on)
    segment_counter += 1
    new_task_name = f"segment_{segment_counter}"
    active_tasks.add(new_task_name)
    task.unique(new_task_name)
    fade_segment_lifecycle(segment_counter)

    # Wait for the rest of the stay duration
    remaining_stay = stay_duration - spawn_delay
    if remaining_stay > 0:
        if not await interruptible_sleep(remaining_stay):
            active_tasks.discard(task_name)
            return

    # FADE OUT
    num_steps = int(FADE_OUT_SECONDS * FADE_STEPS_PER_SECOND)
    step_duration = FADE_OUT_SECONDS / num_steps

    for step in range(num_steps + 1):
        if not running:
            active_tasks.discard(task_name)
            return

        progress = step / num_steps
        brightness = int(LED_BRIGHTNESS * ease_in_out(1.0 - progress))

        led_array = []
        hex_color = f"{brightness:02x}{brightness:02x}{brightness:02x}"
        for led_index in led_indices:
            led_array.extend([led_index, hex_color])

        payload = {"seg": {"id": SEGMENT_ID, "i": led_array, "bri": 255}}
        await send_wled_command_async(payload)

        await task.sleep(step_duration)

    # Clear LEDs
    led_array = []
    for led_index in led_indices:
        led_array.extend([led_index, "000000"])

    payload = {"seg": {"id": SEGMENT_ID, "i": led_array, "bri": 255}}
    await send_wled_command_async(payload)

    # Unregister this segment only after fade-out completes
    active_segments.pop(segment_id, None)
    active_tasks.discard(task_name)

    log.info(f"Segment {segment_id} complete")


async def run_effect():
    """Main effect loop"""
    global segment_counter, active_tasks

    target_segments = random.randint(NUM_SEGMENTS_MIN, NUM_SEGMENTS_MAX)

    log.info(f"Starting {target_segments} initial segments")

    # Start initial segments
    for i in range(target_segments):
        segment_counter += 1
        task_name = f"segment_{segment_counter}"
        active_tasks.add(task_name)
        log.info(f"Creating segment {segment_counter}")
        # Set unique task context and call
        task.unique(task_name)
        fade_segment_lifecycle(segment_counter)
        await task.sleep(random.uniform(0.5, 1.5))

    # Keep running
    while running:
        await task.sleep(10)
