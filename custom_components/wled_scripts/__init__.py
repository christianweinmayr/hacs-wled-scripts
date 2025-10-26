"""WLED Scripts integration for Home Assistant."""
from pathlib import Path
import logging
import shutil

_LOGGER = logging.getLogger(__name__)

DOMAIN = "wled_scripts"


async def async_setup(hass, config):
    """Set up the WLED Scripts component."""
    _LOGGER.info("WLED Scripts integration loaded")

    # Copy pyscript files to the pyscript directory if it exists
    config_dir = Path(hass.config.path())
    pyscript_dir = config_dir / "pyscript"
    source_dir = Path(__file__).parent / "pyscript"

    if pyscript_dir.exists() and source_dir.exists():
        try:
            for script_file in source_dir.glob("*.py"):
                dest_file = pyscript_dir / script_file.name
                shutil.copy2(script_file, dest_file)
                _LOGGER.info(f"Copied {script_file.name} to pyscript directory")
        except Exception as e:
            _LOGGER.warning(f"Could not copy pyscript files: {e}")
            _LOGGER.info("You can manually copy files from custom_components/wled_scripts/pyscript/ to your pyscript/ directory")
    else:
        _LOGGER.warning("Pyscript directory not found. Please ensure Pyscript integration is installed.")
        _LOGGER.info("After installing Pyscript, manually copy files from custom_components/wled_scripts/pyscript/ to your config/pyscript/ directory")

    return True
