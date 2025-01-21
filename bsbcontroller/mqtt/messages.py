from ..telegram.fields import OpMode

from . import templates as tl
from .templates import Template as T


list_hc_modes = list(OpMode.values.values())

boiler_requests: dict[str, T] = {
    "room1_temp":               T(tl.meas),
    "room2_temp":               T(tl.meas),
    "outer_temp":               T(tl.meas),
    "boiler_temp":              T(tl.temp | tl.prec(2)),
    "boiler_return_temp":       T(tl.temp | tl.prec(2)),
    "flue_temp":                T(tl.temp | tl.prec(2)),
    "boiler_water_temp":        T(tl.temp | tl.prec(2)),
    "pump_modulation_pct":      T(tl.base | tl.power_factor),
    "burner_modulation_pct":    T(tl.base | tl.power_factor),
    "burner_start_count":       T(tl.base | tl.total_increasing),
    "gas_consumption":          T(tl.base | tl.total_increasing | tl.energy),
    "water_pressure":           T(tl.meas | tl.pressure),
    "hc_boiler_status":         T(tl.base),
    "hc1_mode":                 T(tl.base),
    "hc2_mode":                 T(tl.base),
    "room1_temp_req":           T(tl.temp | tl.req_temp, component="number"),
    "room2_temp_req":           T(tl.temp | tl.req_temp, component="number"),
    "hc1_operating_mode":       T(tl.base | tl.req | {"options": list_hc_modes}, component="select"),
    "hc2_operating_mode":       T(tl.base | tl.req | {"options": list_hc_modes}, component="select"),
    "hc2_enabled":              T(tl.base | tl.req | tl.switch, component="switch"),
    "hot_water_push":           T(tl.base | tl.req | tl.button, component="button"),
    "hc1_rampup_max_temp":      T(tl.temp | tl.req_temp | dict(min=30, max=60, step=2), component="number"),
    "hc2_rampup_max_temp":      T(tl.temp | tl.req_temp | dict(min=30, max=60, step=2), component="number"),
}
