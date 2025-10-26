# WLED Effect Scripts for Home Assistant

Custom Python scripts for controlling WLED matrix displays with advanced fade effects, designed for Home Assistant using Pyscript.

## Features

- **Smooth Fade Effects**: Independent segments that fade in and out randomly
- **Configurable Parameters**: Adjust fade speeds, segment counts, and timings
- **Overlap Prevention**: Intelligent spacing to prevent flickering
- **Dashboard Control**: Start/stop effects directly from your Home Assistant dashboard

## Prerequisites

1. **Pyscript Integration** - Install via HACS:
   - Go to HACS → Integrations
   - Search for "Pyscript Python scripting"
   - Install and restart Home Assistant

2. **WLED Device** - A working WLED installation on an LED matrix

## Installation

### Via HACS (Recommended)

1. Ensure **Pyscript integration** is installed first (see Prerequisites)

2. Add this repository to HACS:
   - Go to HACS → Integrations → ⋮ (three dots) → Custom repositories
   - Add repository URL: `https://github.com/christianweinmayr/hacs-wled-scripts`
   - Category: `Integration`
   - Click "Add"

3. Install the integration:
   - Find "WLED Effect Scripts" in HACS
   - Click "Download"
   - Restart Home Assistant

4. The integration will automatically copy scripts to your `/config/pyscript/` directory
   - If auto-copy fails, manually copy from `/config/custom_components/wled_scripts/pyscript/` to `/config/pyscript/`

### Manual Installation

1. Ensure Pyscript is installed and configured
2. Download this repository
3. Copy the entire `custom_components/wled_scripts/` folder to `/config/custom_components/`
4. Copy `custom_components/wled_scripts/pyscript/wled_fade_effect.py` to `/config/pyscript/`
5. Restart Home Assistant

## Configuration

### 1. Edit Script Parameters

After installation, edit `/config/pyscript/wled_fade_effect.py` and modify these variables:

```python
# Your WLED device IP
WLED_IP = "10.0.42.15"

# WLED segment ID
SEGMENT_ID = 1

# Matrix coordinates
START_X = 0
STOP_X = 4       # For a 5-LED wide matrix
START_Y = 80
STOP_Y = 139     # For 60 rows

# Effect parameters
NUM_SEGMENTS_MIN = 3              # Minimum active segments
NUM_SEGMENTS_MAX = 6              # Maximum active segments
SEGMENT_LENGTH_MIN = 3            # Minimum rows per segment
SEGMENT_LENGTH_MAX = 5            # Maximum rows per segment
FADE_IN_SECONDS = 20              # Fade in duration
STAY_ON_MIN = 30                  # Min time to stay on
STAY_ON_MAX = 60                  # Max time to stay on
FADE_OUT_SECONDS = 20             # Fade out duration
FADE_STEPS_PER_SECOND = 5         # Update rate (higher = smoother but more traffic)
LED_BRIGHTNESS = 255              # Maximum brightness
```

### 2. Create Helper Entities (Optional but Recommended)

Add to `configuration.yaml`:

```yaml
input_boolean:
  wled_fade_effect:
    name: WLED Fade Effect
    icon: mdi:lightbulb-group
```

### 3. Create Automation

Create an automation to sync the helper with the script state:

```yaml
automation:
  - alias: "WLED Fade Effect Control"
    trigger:
      - platform: state
        entity_id: input_boolean.wled_fade_effect
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: input_boolean.wled_fade_effect
                state: "on"
            sequence:
              - service: pyscript.wled_fade_start
          - conditions:
              - condition: state
                entity_id: input_boolean.wled_fade_effect
                state: "off"
            sequence:
              - service: pyscript.wled_fade_stop
```

## Usage

### Via Services

Call these services directly:

```yaml
# Start the effect
service: pyscript.wled_fade_start

# Stop the effect
service: pyscript.wled_fade_stop
```

### Via Dashboard

Add a button card to your dashboard:

```yaml
type: button
name: WLED Fade Effect
entity: input_boolean.wled_fade_effect
show_state: true
tap_action:
  action: toggle
```

Or use an entities card:

```yaml
type: entities
entities:
  - entity: input_boolean.wled_fade_effect
    name: WLED Fade Effect
```

## Dashboard Example

Here's a complete Lovelace card configuration:

```yaml
type: vertical-stack
cards:
  - type: entities
    title: WLED Effects
    entities:
      - entity: input_boolean.wled_fade_effect
        name: Fade Effect
        secondary_info: last-changed

  - type: markdown
    content: |
      **Status**: {% if is_state('input_boolean.wled_fade_effect', 'on') %}🟢 Running{% else %}⭕ Stopped{% endif %}

      Effect creates 3-6 random segments that fade in/out independently on your WLED matrix.
```

## Troubleshooting

### Script not starting

1. Check Pyscript is properly installed and loaded
2. Check Home Assistant logs for errors: Settings → System → Logs
3. Verify your WLED IP address is correct in the script

### LEDs flickering

- Reduce `FADE_STEPS_PER_SECOND` (try 3-5)
- Increase `MIN_SPACING` in the script
- Check your network stability

### Effect is too fast/slow

- Adjust `FADE_IN_SECONDS` and `FADE_OUT_SECONDS`
- Modify `STAY_ON_MIN` and `STAY_ON_MAX`

## Adding More Scripts

To add more WLED effect scripts in the future:

1. Create a new `.py` file in the `/config/pyscript/` directory
2. Follow the same pattern as `wled_fade_effect.py`
3. Expose services using the `@service` decorator
4. Create corresponding helper entities and automation
5. Or add them to this integration's `custom_components/wled_scripts/pyscript/` directory and update the `__init__.py` to copy them

## License

MIT License - Feel free to modify and distribute

## Credits

Created for use with [WLED](https://github.com/Aircoookie/WLED) and [Home Assistant](https://www.home-assistant.io/)

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
