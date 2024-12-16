from .types import Flag
from .datatypes import TFDate, TFError, TFHCStat, TFHWater, TFStatB, TFStatHW, TFOnOff, TFEnable, TFTemp, TFInt8, TF10Float, TFInt16, TFInt32, TFOpMode, TFCStatus, TFSchedule, TFPct2


FB = Flag.FB
LB = Flag.LB
NN = Flag.NONE
SB = Flag.IF | Flag.BC
LI = Flag.IF | Flag.LB
QI = Flag.QI

i2d = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

#   0x10000000 # flag
#   0x20000000 # writable flag?
#   0x08000000 # indexable flag?
#   0x07000000 # index mask?
messages = {
    # Identification:
    # 0x008500DD ...: QAA75.910/349
    # 0x007B00E7 ...: Baxi Luna Platinum+ 1.24
    0x05000064: (NN, None,      "identify"),
    #0x05050064: (NN, None,      "identify"), # Request from T1
    0x053d0248: (NN, None,      "unknown1"),
    0x0500006c: (SB, TFDate,    "datetime"),
    0x0500006b: (NN, TFError,   "error"),
    0x2d000211: (NN, TFHCStat,  "hc1_status"), # This is for INF K->B. For QUR and ANS is used 0x2d3d0211
    0x2e000211: (NN, TFHCStat,  "hc2_status"),
    0x2f000211: (NN, TFHCStat,  "hc3_status"),
    0x2d3d0211: (NN, TFHCStat,  "hc1_status_qa"),
    0x2e3e0211: (QI, TFHCStat,  "hc2_status_qa"),
    0x2f3f0211: (NN, TFHCStat,  "hc3_status_qa"),
    0x31000212: (FB, TFHWater,  "hot_water_status"), # This is for INF. For QUR and ANS is used 0x313d0212
    0x313d0212: (FB, TFHWater,  "hot_water_status_qa"),
    0x05000213: (NN, TFStatB,   "status_burner"),
    0x053d0213: (NN, TFStatB,   "status_burner"), # Request from T1
    0x3d2d0215: (LI, TFTemp,    "room1_temp_status"), # This is for INF T->K
    0x3e2e0215: (LI, TFTemp,    "room2_temp_status"),
    0x05000219: (NN, TFStatHW,  "status_hw"),
    0x053d0219: (NN, TFStatHW,  "status_hw_qa"), # Request from T1
    #0x053d0219: The same, but as ans to QUR
    0x053d0236: (FB, TFOnOff,   "standby"),
    0x053d04c0: (FB, TFEnable,  "hc1_enabled"),
    0x063d04c0: (FB, TFEnable,  "hc2_enabled"),
    0x073d04c0: (FB, TFEnable,  "hc3_enabled"),
    0x0d3d0519: (FB, TFTemp,    "boiler_temp"),
    0x113d051a: (FB, TFTemp,    "boiler_return_temp"),
    0x053d051d: (FB, TFTemp,    "flue_temp"),
    0x2d3d051e: (FB, TFTemp,    "room1_temp"),
    #0x2e3e051e: (FB, TFTemp,    "room2_temp"),
    0x2e3d051e: (FB, TFTemp,    "room2_temp"), # This is readen from T1
    0x053d0521: (FB, TFTemp,    "outer_temp"),
    0x313d052f: (FB, TFTemp,    "boiler_water_temp"),
    0x053d056f: (FB, TFTemp,    "outer_temp_min"),
    0x053d056e: (FB, TFTemp,    "outer_temp_max"),
    0x313d0571: (FB, TFOnOff,   "hot_water_operating_mode"),
    0x313d0573: (FB, TFOnOff,   "hot_water_push"),
    0x2d3d0574: (FB, TFOpMode,  "hc1_operating_mode"),
    0x2e3d0574: (FB, TFOpMode,  "hc2_operating_mode"),
    0x2d3d058e: (FB, TFTemp,    "room1_req_comfort_temp"),
    0x2e3d058e: (FB, TFTemp,    "room2_req_comfort_temp"),
    0x2d3d0590: (FB, TFTemp,    "room1_req_reduced_temp"),
    0x2e3d0590: (FB, TFTemp,    "room2_req_reduced_temp"),
    0x2d3d0592: (FB, TFTemp,    "hc1_temp_antifreeze"),
    0x2e3d0593: (FB, TFTemp,    "room2_setpoint"),
    0x2d3d0593: (FB, TFTemp,    "room1_requested_temp"), # room1_setpoint
    0x2d3d05a5: (FB, TFTemp,    "hc1_temp_comfort_max"),
    0x2d3d05f6: (FB, None,      "hc1_curve_steep"),
    0x2d3d0603: (FB, TFInt8,    "hc1_room_influence_ptc"),
    0x2d3d060b: (FB, TFEnable,  "hc1_curve_adaptation"),
    0x2d3d0610: (FB, None,      "hc1_curve_offset"),
    0x3d210662: (FB, TFTemp,    "hc1_rampup_temp"),
    0x213d0662: (FB, TFTemp,    "hc1_rampup_max_temp"),
    0x313d06b9: (FB, TFTemp,    "req_hot_water_nominal_temp"),
    0x313d06ba: (FB, TFTemp,    "req_hot_water_reduced_temp"),
    0x053d06e8: (NN, None,      "phone_number"), # 30 30 30 30 30 30 31 31 30 30 30 00 00 00 00 00
    0x313d074b: (FB, TFTemp,    "req_hot_water_temp"),
    0x313d0759: (FB, None,      "legionella_function"),
    0x053d07a1: (FB, TFCStatus, "hot_water_status_info"),
    0x053d07a2: (FB, TFCStatus, "hot_water_state"), # Information menu
    0x053d07a3: (FB, TFCStatus, "hc1_mode"), # 8000 # State menu: state central heating
    0x053d07a4: (FB, TFCStatus, "hc1_state_central_heating"), # Information menu
    0x053d07a5: (FB, TFCStatus, "hc2_mode"), # 8001 # state central heating
    0x053d07a6: (FB, TFCStatus, "hc2_state_central_heating"), # Information menu
    0x053d07a7: (FB, TFCStatus, "hc3_mode"), # 8002 # state central heating
    0x053d07a9: (FB, TFCStatus, "boiler_status"), # State menu
    0x053d07aa: (FB, TFCStatus, "hc_boiler_status"), # Information menu
    0x053d0805: (FB, TF10Float, "water_pressure"),
    0x053d0826: (FB, TFInt8,    "pump_modulation_pct"),
    0x053d0834: (FB, TFInt8,    "burner_modulation_pct"),
    0x053d08a5: (FB, TFInt32,   "burner_start_count"),
    0x0d3d093b: (FB, TFInt32,   "first_stage_op_time"),
    0x053d09a3: (FB, TFEnable,  "hw_pump"),
    0x053d09a5: (FB, TFEnable,  "hc1_pump"),
    0x053d0a73: (FB, TFEnable,  "cc1_enabled"), # cooling circuit
    0x213d0a88: (FB, TFTemp,    "hc1_flow_temp_setpoint_room_stat"), # FIXME
    **(lambda TFSchedule=TFSchedule: {0x053d0a8c + i: (NN, TFSchedule, "hc1_time_prog_{0}".format(i2d[i])) for i in range(7)})(),
    **(lambda TFSchedule=TFSchedule: {0x053d0aa0 + i: (NN, TFSchedule, "hot_water_time_prog_{0}".format(i2d[i])) for i in range(7)})(),
    0x093d0dfd: (FB, TFCStatus, "burner_current_phase"), # [0x10] = modulace, 4=STY, 2=TLO?
    0x093d0e00: (FB, TFPct2,    "fan_modulation_pct"),
    0x093d0e16: (FB, TFInt16,   "burner_ionisation_current"), # Vydel 100 a mas hodnotu v uA
    0x093d0e69: (FB, TFInt16,   "fan_rpm"),
    0x093d0f62: (FB, None,      "sitherm_operating_phase"), # 03=Standby 07: nadrazena regulace, 08 stabilizace 12 ADA 1 interval uplynul
    0x053d0f66: (FB, TFCStatus, "burner_state"),
    0x053d0f8e: (NN, None,      "hot_water_flow"),
    0x053d1071: (FB, TFTemp,    "primary_temp"), # FIXME
    0x2d3d1125: (FB, TFTemp,    "room1_temp_req"),
    0x2e3e1125: (FB, TFTemp,    "room2_temp_req"),
    #0x053d1771 |00 00 00 27 75| Switch to RoomThermo 2
    0x053d1289: (FB, TFEnable,  "hc1_continuous_pump_operation"),
    0x053d1a7a: (FB, TFInt32,   "gas_consumption_heating"),
    0x053d1a7b: (FB, TFInt32,   "gas_consumption_hot_water"),
    0x053d1a7c: (FB, TFInt32,   "gas_consumption"),
    0x053d1ac1: (FB, None,      "sitherm_pro_state"), # 00 = off, 0x12: v provozu
    0x053d1ac2: (FB, None,      "SithermPro_state"), # data[1] is common status value
    0x053d2feb: (FB, TFInt32,   "hc_op_time"),
    0x053d2fec: (FB, TFInt32,   "hot_water_op_time"),
    0x053d3063: (FB, TFInt16,   "burner_water_pressure"),
    0x053d3043: (FB, TFInt16,   "gas_quality"),
}

messages_by_name = {v[2]: k for k, v in messages.items()}
rows = {k & 0xffff: k for k in messages.keys()}
