import logging

import pytz

utc=pytz.UTC


from homeassistant.core import (HomeAssistant, callback)
from homeassistant.helpers.entity import generate_entity_id

from homeassistant.helpers.update_coordinator import (
  CoordinatorEntity,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass
)
from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.util.dt import (now)

from ..api_client import HarvestApiClient

from . import async_create_time_entry_with_hours, get_todays_hours

_LOGGER = logging.getLogger(__name__)

class HarvestHoursToday(CoordinatorEntity, SensorEntity, RestoreEntity):
  """Sensor for determining the total hours from today"""

  def __init__(self, hass: HomeAssistant, coordinator, account_id: str, client: HarvestApiClient):
    """Init sensor."""

    super().__init__(coordinator)
  
    self._state = None
    self._attributes = {
      "account_id": account_id
    }
    self._account_id = account_id
    self._client = client

    self.entity_id = generate_entity_id("sensor.{}", self.unique_id, hass=hass)

  @property
  def unique_id(self):
    """The id of the sensor."""
    return f"harvest_time_tracker_{self._account_id}_hours_today"
    
  @property
  def name(self):
    """Name of the sensor."""
    return f"Harvest Hours Today ({self._account_id})"

  @property
  def icon(self):
    """Icon of the sensor."""
    return "mdi:clock"

  @property
  def extra_state_attributes(self):
    """Attributes of the sensor."""
    return self._attributes

  @property
  def state_class(self):
    """The state class of sensor"""
    return SensorStateClass.TOTAL_INCREASING

  @property
  def state(self):
    """Calculate the correct hours"""
    entries = self.coordinator.data
    
    result = get_todays_hours(now(), entries)
    self._state = result.hours
    self._attributes["entries"] = result.entries

    return self._state

  async def async_added_to_hass(self):
    """Call when entity about to be added to hass."""
    # If not None, we got an initial value.
    await super().async_added_to_hass()
    state = await self.async_get_last_state()

    if state is not None and self._state is None:
      self._state = state.state
      self._attributes = {}
      for x in state.attributes.keys():
        self._attributes[x] = state.attributes[x]
    
      _LOGGER.debug(f'Restored HarvestHoursToday state: {self._state}')

  @callback
  async def async_add_time_with_hours(self, project_id: int, task_id: int, date: str, hours: str, notes: str = None):
    """Create time entry"""

    await async_create_time_entry_with_hours(self._client, project_id, task_id, date, hours, notes)