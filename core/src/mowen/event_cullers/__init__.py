"""Built-in event cullers for the mowen pipeline."""

from mowen.event_cullers.base import EventCuller, event_culler_registry

# Import implementation modules so their @register decorators execute.
from mowen.event_cullers import coefficient_of_variation as coefficient_of_variation
from mowen.event_cullers import information_gain as information_gain
from mowen.event_cullers import iqr as iqr
from mowen.event_cullers import least_common as least_common
from mowen.event_cullers import most_common as most_common
from mowen.event_cullers import percentage_range as percentage_range
from mowen.event_cullers import range_culler as range_culler
from mowen.event_cullers import std_deviation as std_deviation
from mowen.event_cullers import variance as variance

__all__ = ["EventCuller", "event_culler_registry"]
