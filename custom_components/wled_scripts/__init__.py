"""WLED Scripts integration for Home Assistant."""
from __future__ import annotations

from pathlib import Path
import logging
import shutil

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WLED Scripts from a config entry."""
    _LOGGER.info("Setting up WLED Scripts integration")

    # Copy pyscript files to the pyscript directory
    config_dir = Path(hass.config.path())
    pyscript_dir = config_dir / "pyscript"
    source_dir = Path(__file__).parent / "pyscript"

    # Create pyscript directory if it doesn't exist
    if not pyscript_dir.exists():
        try:
            await hass.async_add_executor_job(pyscript_dir.mkdir, True, True)
            _LOGGER.info("Created pyscript directory")
        except Exception as e:
            _LOGGER.error(f"Could not create pyscript directory: {e}")
            return False

    # Copy script files
    if source_dir.exists():
        try:
            copied_files = []
            for script_file in source_dir.glob("*.py"):
                dest_file = pyscript_dir / script_file.name
                # Use executor to run blocking file operations
                await hass.async_add_executor_job(shutil.copy2, script_file, dest_file)
                copied_files.append(script_file.name)
                _LOGGER.info(f"Copied {script_file.name} to pyscript directory")

            if copied_files:
                _LOGGER.info(f"Successfully copied {len(copied_files)} script(s) to pyscript directory")
                _LOGGER.warning("Please reload Pyscript or restart Home Assistant for the scripts to load")
            else:
                _LOGGER.warning("No script files found to copy")
        except Exception as e:
            _LOGGER.error(f"Error copying pyscript files: {e}")
            return False
    else:
        _LOGGER.error(f"Source directory not found: {source_dir}")
        return False

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading WLED Scripts integration")
    return True
