"""Custom integration to integrate Petkit Smart Devices with Home Assistant."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from pypetkitapi import PetKitClient

from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_TIME_ZONE,
    CONF_USERNAME,
    Platform,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .const import (
    BT_SECTION,
    CONF_BLE_RELAY_ENABLED,
    CONF_DELETE_AFTER,
    CONF_MEDIA_DL_IMAGE,
    CONF_MEDIA_DL_VIDEO,
    CONF_MEDIA_EV_TYPE,
    CONF_MEDIA_PATH,
    CONF_SCAN_INTERVAL_BLUETOOTH,
    CONF_SCAN_INTERVAL_MEDIA,
    COORDINATOR,
    COORDINATOR_BLUETOOTH,
    COORDINATOR_MEDIA,
    DEFAULT_BLUETOOTH_RELAY,
    DEFAULT_DELETE_AFTER,
    DEFAULT_DL_IMAGE,
    DEFAULT_DL_VIDEO,
    DEFAULT_EVENTS,
    DEFAULT_MEDIA_PATH,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_BLUETOOTH,
    DEFAULT_SCAN_INTERVAL_MEDIA,
    DOMAIN,
    LOGGER,
    MEDIA_SECTION,
)
from .coordinator import (
    PetkitBluetoothUpdateCoordinator,
    PetkitDataUpdateCoordinator,
    PetkitMediaUpdateCoordinator,
)
from .data import PetkitData
from .iot_mqtt import PetkitIotMqttListener
from .whep_mirror import (
    PetkitInternalWhepMirrorView,
    PetkitWhepMirrorView,
    async_cleanup_whep_mirror_sessions,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .data import PetkitConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.TEXT,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.IMAGE,
    Platform.FAN,
]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entry to current version.

    Handles migration from home-assistant-petkit versions 1-5 (which used
    CONF_EMAIL, separate options for region/timezone/polling) to the current
    schema at version 7 (which uses CONF_USERNAME with data containing region
    and timezone, and structured options sections).
    """

    if entry.version in [1, 2, 3]:
        # Versions 1-3: email/password in data, polling_interval in options,
        # no region or timezone stored.
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]

        LOGGER.debug("Migrating PetKit config entry from version %s", entry.version)

        hass.config_entries.async_update_entry(
            entry,
            version=7,
            data={
                CONF_USERNAME: email,
                CONF_PASSWORD: password,
                CONF_REGION: hass.config.country,
                CONF_TIME_ZONE: hass.config.time_zone,
            },
            options={
                MEDIA_SECTION: {
                    CONF_MEDIA_PATH: DEFAULT_MEDIA_PATH,
                    CONF_SCAN_INTERVAL_MEDIA: DEFAULT_SCAN_INTERVAL_MEDIA,
                    CONF_MEDIA_DL_IMAGE: DEFAULT_DL_IMAGE,
                    CONF_MEDIA_DL_VIDEO: DEFAULT_DL_VIDEO,
                    CONF_MEDIA_EV_TYPE: DEFAULT_EVENTS,
                    CONF_DELETE_AFTER: DEFAULT_DELETE_AFTER,
                },
                BT_SECTION: {
                    CONF_BLE_RELAY_ENABLED: DEFAULT_BLUETOOTH_RELAY,
                    CONF_SCAN_INTERVAL_BLUETOOTH: DEFAULT_SCAN_INTERVAL_BLUETOOTH,
                },
            },
        )
        LOGGER.warning(
            "PetKit config entry migrated from version %s to 7. "
            "Region was set from HA config. Please verify in integration options.",
            entry.version,
        )

    if entry.version in [4, 5]:
        # Versions 4-5: email/password in data, region/timezone/polling in options.
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]
        # Old const names: REGION, TIMEZONE, POLLING_INTERVAL, USE_BLE_RELAY
        region = entry.options.get("region", hass.config.country)
        timezone = entry.options.get("timezone", hass.config.time_zone)
        ble_relay = entry.options.get("use_ble_relay", DEFAULT_BLUETOOTH_RELAY)

        LOGGER.debug("Migrating PetKit config entry from version %s", entry.version)

        hass.config_entries.async_update_entry(
            entry,
            version=7,
            data={
                CONF_USERNAME: email,
                CONF_PASSWORD: password,
                CONF_REGION: region,
                CONF_TIME_ZONE: timezone,
            },
            options={
                MEDIA_SECTION: {
                    CONF_MEDIA_PATH: DEFAULT_MEDIA_PATH,
                    CONF_SCAN_INTERVAL_MEDIA: DEFAULT_SCAN_INTERVAL_MEDIA,
                    CONF_MEDIA_DL_IMAGE: DEFAULT_DL_IMAGE,
                    CONF_MEDIA_DL_VIDEO: DEFAULT_DL_VIDEO,
                    CONF_MEDIA_EV_TYPE: DEFAULT_EVENTS,
                    CONF_DELETE_AFTER: DEFAULT_DELETE_AFTER,
                },
                BT_SECTION: {
                    CONF_BLE_RELAY_ENABLED: ble_relay,
                    CONF_SCAN_INTERVAL_BLUETOOTH: DEFAULT_SCAN_INTERVAL_BLUETOOTH,
                },
            },
        )

    if entry.version == 6:
        # Version 6: from home-assistant-petkit, similar to 4-5 but at version 6.
        email = entry.data.get(CONF_EMAIL, entry.data.get(CONF_USERNAME))
        password = entry.data[CONF_PASSWORD]
        region = entry.options.get("region", hass.config.country)
        timezone = entry.options.get("timezone", hass.config.time_zone)
        ble_relay = entry.options.get("use_ble_relay", DEFAULT_BLUETOOTH_RELAY)

        LOGGER.debug("Migrating PetKit config entry from version 6")

        hass.config_entries.async_update_entry(
            entry,
            version=7,
            data={
                CONF_USERNAME: email,
                CONF_PASSWORD: password,
                CONF_REGION: region,
                CONF_TIME_ZONE: timezone,
            },
            options={
                MEDIA_SECTION: {
                    CONF_MEDIA_PATH: DEFAULT_MEDIA_PATH,
                    CONF_SCAN_INTERVAL_MEDIA: DEFAULT_SCAN_INTERVAL_MEDIA,
                    CONF_MEDIA_DL_IMAGE: DEFAULT_DL_IMAGE,
                    CONF_MEDIA_DL_VIDEO: DEFAULT_DL_VIDEO,
                    CONF_MEDIA_EV_TYPE: DEFAULT_EVENTS,
                    CONF_DELETE_AFTER: DEFAULT_DELETE_AFTER,
                },
                BT_SECTION: {
                    CONF_BLE_RELAY_ENABLED: ble_relay,
                    CONF_SCAN_INTERVAL_BLUETOOTH: DEFAULT_SCAN_INTERVAL_BLUETOOTH,
                },
            },
        )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PetkitConfigEntry,
) -> bool:
    """Set up this integration using UI."""

    # Register API views once (idempotent — HA deduplicates by name)
    hass.http.register_view(PetkitInternalWhepMirrorView())
    hass.http.register_view(PetkitWhepMirrorView())

    country_from_ha = hass.config.country
    tz_from_ha = hass.config.time_zone

    coordinator = PetkitDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=f"{DOMAIN}.devices",
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        config_entry=entry,
    )
    coordinator_media = PetkitMediaUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=f"{DOMAIN}.medias",
        update_interval=timedelta(
            minutes=entry.options[MEDIA_SECTION][CONF_SCAN_INTERVAL_MEDIA]
        ),
        config_entry=entry,
        data_coordinator=coordinator,
    )
    coordinator_bluetooth = PetkitBluetoothUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=f"{DOMAIN}.bluetooth",
        update_interval=timedelta(
            minutes=entry.options[BT_SECTION][CONF_SCAN_INTERVAL_BLUETOOTH]
        ),
        config_entry=entry,
        data_coordinator=coordinator,
    )
    entry.runtime_data = PetkitData(
        client=PetKitClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            region=entry.data.get(CONF_REGION, country_from_ha),
            timezone=entry.data.get(CONF_TIME_ZONE, tz_from_ha),
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        coordinator_media=coordinator_media,
        coordinator_bluetooth=coordinator_bluetooth,
    )

    await coordinator.async_config_entry_first_refresh()
    await coordinator_media.async_config_entry_first_refresh()
    await coordinator_bluetooth.async_config_entry_first_refresh()

    # MQTT

    mqtt_listener = PetkitIotMqttListener(
        hass=hass,
        client=entry.runtime_data.client,
        coordinator=coordinator,
    )

    entry.runtime_data.mqtt_listener = mqtt_listener
    await mqtt_listener.async_start()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][COORDINATOR] = coordinator
    hass.data[DOMAIN][COORDINATOR_MEDIA] = coordinator
    hass.data[DOMAIN][COORDINATOR_BLUETOOTH] = coordinator

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: PetkitConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    mqtt_listener = getattr(entry.runtime_data, "mqtt_listener", None)
    if mqtt_listener is not None:
        await mqtt_listener.async_stop()

    await async_cleanup_whep_mirror_sessions(hass)

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: PetkitConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_update_options(hass: HomeAssistant, entry: PetkitConfigEntry) -> None:
    """Update options."""

    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: PetkitConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True
