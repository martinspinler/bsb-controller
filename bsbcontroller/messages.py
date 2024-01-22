from .types import Flag
from .datatypes import *

FB = Flag.FB
LB = Flag.LB
NN = Flag.NONE

def i2d(i):
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    return days[i]

messages = {
    # Identification: 
    # 0x008500DD ...: QAA75.910/349
    # 0x007B00E7 ...: Baxi Luna Platinum+ 1.24
    0x05000064: (NN, None,      "identify"),
    0x053d0248: (NN, None,      "unknown1"),
    0x0500006c: (NN, TTDate,    "datetime"),
    0x0500006b: (NN, TTError,   "error"),
    0x31000212: (FB, TTHotWater,"hot_water_status"),
    0x3d2d0215: (LB, TTTemp,    "room1_temp_status"),
    0x2d000211: (NN, None,      "hc1_status"),
    0x2e000211: (NN, None,      "hc2_status"),
    0x2f000211: (NN, None,      "hc3_status"),
    0x05000213: (NN, TTStat1,   "status_msg1"),
    0x05000219: (NN, TTStat2,   "status_msg2"),
    0x0d3d0519: (FB, TTTemp,    "boiler_temp"),
    0x113d051a: (FB, TTTemp,    "boiler_return_temp"),
    0x053d051d: (FB, TTTemp,    "flue_temp"),
    0x053d0521: (FB, TTTemp,    "outer_temp"),
    0x313d052f: (FB, TTTemp,    "boiler_water_temp"),
    0x053d056f: (FB, TTTemp,    "outer_temp_min"),
    0x053d056e: (FB, TTTemp,    "outer_temp_max"),
    0x313d0571: (NN, TTOnOff,   "hot_water_operating_mode"), # FIXME
    0x2d3d0574: (FB, TTOpLvl,   "hc1_operating_level"),
    0x2d3d058e: (FB, TTTemp,    "req_room_comfort_temp"),
    0x2d3d0590: (FB, TTTemp,    "req_room_reduced_temp"),
    0x3d210662: (FB, TTTemp,    "hc1_rampup_temp"),
    0x313d06b9: (FB, TTTemp,    "req_hot_water_nominal_temp"),
    0x313d06ba: (FB, TTTemp,    "req_hot_water_reduced_temp"),
    0x313d074b: (FB, TTTemp,    "req_hot_water_temp"),
    0x053d06e8: (NN, None,      "phone_number"),
    0x053d07a2: (NN, None,      "hot_water_status2"),
    0x053d07aa: (NN, None,      "hc_boilter_status"),
    0x053d07a4: (NN, None,      "hc_mode"),
    0x053d07a9: (NN, None,      "boiler_status"),
    0x053d0805: (FB, TT10Float, "water_pressure"), #9005
    0x053d0826: (FB, TTPct,     "pump_modulation_pct"),
    0x053d0834: (FB, TTPct,     "burner_modulation_pct"),
    0x053d08a5: (FB, TTInt32,   "burner_start_count"),
    0x213d0a88: (FB, TTTemp,    "rampup_temp"), # FIXME
    0x2d3d051e: (FB, TTTemp,    "room1_temp"),
    0x2d3d0593: (FB, TTTemp,    "room1_requested_temp"), #FIXME
    0x053d0f8e: (NN, None,      "hot_water_flow"),
    **(lambda TTSchedule = TTSchedule: {0x053d0a8c + i: (NN, TTSchedule, "hc1_time_prog_{0}".format(i2d(i))) for i in range(7)})(),
    **(lambda TTSchedule = TTSchedule: {0x053d0aa0 + i: (NN, TTSchedule, "hot_water_time_prog_{0}".format(i2d(i))) for i in range(7)})(),
    0x2d3d1125: (FB, TTTemp,    "req_room_temp"),
    0x053d1071: (FB, TTTemp,    "primary_temp"), # FIXME
    0x053d1a7a: (FB, TTInt32,   "gas_consumption_heating"),
    0x053d1a7b: (FB, TTInt32,   "gas_consumption_hot_water"),
    0x053d1a7c: (FB, TTInt32,   "gas_consumption"),
    0x053d0f66: (NN, None,      "burner_state"), 
    0x093d0e00: (FB, TTPct2,    "fan_modulation_pct"), # FIXME
    0x093d0e16: (FB, TTInt16,   "burner_ionisation_current"), # Vydel 100 a mas hodnotu v uA
    0x093d0e69: (FB, TTInt16,   "fan_rpm"),
    0x053d3063: (NN, TTInt16,   "burner_water_pressure"), #FIXME : Same ID as below
    0x053d3063: (NN, None,      "burner_phase"), # FIXME: Same ID as above
    0x093d0dfd: (NN, None,      "burner_current_phase"), #[0, 0x10] = modulace, 4=STY, 2=TLO?
    0x0d3d093b: (FB, TTInt32,   "first_stage_op_time"),
    0x053d2feb: (FB, TTInt32,   "hc_op_time"),
    0x053d2fec: (FB, TTInt32,   "hot_water_op_time"),
    0x053d1289: (NN, None,      "pump_permanent_op"),
    0x213d0662: (FB, TTTemp,    "hc1_rampup_max_temp"),
}

messages_by_name = {v[2]: k for k, v in messages.items()}
rows = {k & 0xffff: k for k in messages.keys()}
