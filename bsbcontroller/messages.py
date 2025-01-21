from .telegram import Flag, Message as M
from .telegram import fields as f


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
messages = [
    # Identification:
    # 0x008500DD ...: QAA75.910/349
    # 0x007B00E7 ...: Baxi Luna Platinum+ 1.24
    M(0x05000064, NN, None,         "identify"),
    #M(0x05050064, NN, None,         "identify"), # Request from T1
    M(0x053d0248, NN, None,         "unknown1"),
    M(0x0500006c, SB, f.Date,       "datetime"),
    M(0x0500006b, NN, f.Error,      "error"),
    M(0x2d000211, NN, f.HCStat,     "hc1_status"), # This is for INF K->B. For QUR and ANS is used 0x2d3d0211
    M(0x2e000211, NN, f.HCStat,     "hc2_status"),
    M(0x2f000211, NN, f.HCStat,     "hc3_status"),
    M(0x2d3d0211, NN, f.HCStat,     "hc1_status_qa"),
    M(0x2e3e0211, QI, f.HCStat,     "hc2_status_qa"),
    M(0x2f3f0211, NN, f.HCStat,     "hc3_status_qa"),
    M(0x31000212, FB, f.HWater,     "hot_water_status"), # This is for INF. For QUR and ANS is used 0x313d0212
    M(0x313d0212, FB, f.HWater,     "hot_water_status_qa"),
    M(0x05000213, NN, f.StatB,      "status_burner"),
    M(0x053d0213, NN, f.StatB,      "status_burner"), # Request from T1
    M(0x3d2d0215, LI, f.Temp,       "room1_temp_status"), # This is for INF T->K
    M(0x3e2e0215, LI, f.Temp,       "room2_temp_status"),
    M(0x05000219, NN, f.StatHW,     "status_hw"),
    M(0x053d0219, NN, f.StatHW,     "status_hw_qa"), # Request from T1
    M(0x053d0236, FB, f.OnOff,      "standby"),
    M(0x053d04c0, FB, f.Enable,     "hc1_enabled"),
    M(0x063d04c0, FB, f.Enable,     "hc2_enabled"),
    M(0x073d04c0, FB, f.Enable,     "hc3_enabled"),
    M(0x0d3d0519, FB, f.Temp,       "boiler_temp"),
    M(0x113d051a, FB, f.Temp,       "boiler_return_temp"),
    M(0x053d051d, FB, f.Temp,       "flue_temp"),
    M(0x2d3d051e, FB, f.Temp,       "room1_temp"),
    #M(0x2e3e051e, FB, f.Temp,       "room2_temp"),
    M(0x2e3d051e, FB, f.Temp,       "room2_temp"), # This is readen from T1
    M(0x053d0521, FB, f.Temp,       "outer_temp"),
    M(0x313d052f, FB, f.Temp,       "boiler_water_temp"),
    M(0x053d056f, FB, f.Temp,       "outer_temp_min"),
    M(0x053d056e, FB, f.Temp,       "outer_temp_max"),
    M(0x313d0571, FB, f.OnOff,      "hot_water_operating_mode"),
    M(0x313d0573, FB, f.OnOff,      "hot_water_push"),
    M(0x2d3d0574, FB, f.OpMode,     "hc1_operating_mode"),
    M(0x2e3d0574, FB, f.OpMode,     "hc2_operating_mode"),
    M(0x2d3d058e, FB, f.Temp,       "room1_req_comfort_temp"),
    M(0x2e3d058e, FB, f.Temp,       "room2_req_comfort_temp"),
    M(0x2d3d0590, FB, f.Temp,       "room1_req_reduced_temp"),
    M(0x2e3d0590, FB, f.Temp,       "room2_req_reduced_temp"),
    M(0x2d3d0592, FB, f.Temp,       "hc1_temp_antifreeze"),
    M(0x2e3d0593, FB, f.Temp,       "room2_setpoint"),
    M(0x2d3d0593, FB, f.Temp,       "room1_requested_temp"), # room1_setpoint
    M(0x2d3d05a5, FB, f.Temp,       "hc1_temp_comfort_max"),
    M(0x2d3d05f6, FB, None,         "hc1_curve_steep"),
    M(0x2d3d0603, FB, f.Int8,       "hc1_room_influence_ptc"),
    M(0x2e3d0603, FB, f.Int8,       "hc2_room_influence_ptc"),
    M(0x2d3d060b, FB, f.Enable,     "hc1_curve_adaptation"),
    M(0x2d3d0610, FB, None,         "hc1_curve_offset"),
    M(0x3d210662, FB, f.Temp,       "hc1_rampup_temp"),
    M(0x213d0662, FB, f.Temp,       "hc1_rampup_max_temp"),
    M(0x223d0662, FB, f.Temp,       "hc2_rampup_max_temp"),
    M(0x313d06b9, FB, f.Temp,       "req_hot_water_nominal_temp"),
    M(0x313d06ba, FB, f.Temp,       "req_hot_water_reduced_temp"),
    M(0x053d06e8, NN, None,         "phone_number"), # 30 30 30 30 30 30 31 31 30 30 30 00 00 00 00 00
    M(0x313d074b, FB, f.Temp,       "req_hot_water_temp"),
    M(0x313d0759, FB, None,         "legionella_function"),
    M(0x053d07a1, FB, f.CStatus,    "hot_water_status_info"),
    M(0x053d07a2, FB, f.CStatus,    "hot_water_state"), # Information menu
    M(0x053d07a3, FB, f.CStatus,    "hc1_mode"), # 8000 # State menu: state central heating
    M(0x053d07a4, FB, f.CStatus,    "hc1_state_central_heating"), # Information menu
    M(0x053d07a5, FB, f.CStatus,    "hc2_mode"), # 8001 # state central heating
    M(0x053d07a6, FB, f.CStatus,    "hc2_state_central_heating"), # Information menu
    M(0x053d07a7, FB, f.CStatus,    "hc3_mode"), # 8002 # state central heating
    M(0x053d07a9, FB, f.CStatus,    "boiler_status"), # State menu
    M(0x053d07aa, FB, f.CStatus,    "hc_boiler_status"), # Information menu
    M(0x053d0805, FB, f.Float10,    "water_pressure"),
    M(0x053d0826, FB, f.Int8,       "pump_modulation_pct"),
    M(0x053d0834, FB, f.Int8,       "burner_modulation_pct"),
    M(0x053d08a5, FB, f.Int32,      "burner_start_count"),
    M(0x0d3d093b, FB, f.Int32,      "first_stage_op_time"),
    M(0x053d09a3, FB, f.Enable,     "hw_pump"),
    M(0x053d09a5, FB, f.Enable,     "hc1_pump"),
    M(0x053d0a73, FB, f.Enable,     "cc1_enabled"), # cooling circuit
    M(0x213d0a88, FB, f.Temp,       "hc1_flow_temp_setpoint_room_stat"), # FIXME
    M(0x223d0a88, FB, f.Temp,       "hc2_zadana_teplota_nabehu_prostoroveho_termostatu"),
    *[M(0x053d0a8c + i, NN, f.Schedule, "hc1_time_prog_{0}".format(i2d[i])) for i in range(7)],
    *[M(0x053d0aa0 + i, NN, f.Schedule, "hot_water_time_prog_{0}".format(i2d[i])) for i in range(7)],
    M(0x093d0dfd, FB, f.CStatus,    "burner_current_phase"), # [0x10] = modulace, 4=STY, 2=TLO?
    M(0x093d0e00, FB, f.Pct2,       "fan_modulation_pct"),
    M(0x093d0e16, FB, f.Int16,      "burner_ionisation_current"), # Vydel 100 a mas hodnotu v uA
    M(0x093d0e69, FB, f.Int16,      "fan_rpm"),
    M(0x093d0f62, FB, None,         "sitherm_operating_phase"), # 03=Standby 07: nadrazena regulace, 08 stabilizace 12 ADA 1 interval uplynul
    M(0x053d0f66, FB, f.CStatus,    "burner_state"),
    M(0x053d0f8e, NN, None,         "hot_water_flow"),
    M(0x053d1071, FB, f.Temp,       "primary_temp"), # FIXME
    M(0x2d3d1125, FB, f.Temp,       "room1_temp_req"),
    M(0x2e3e1125, FB, f.Temp,       "room2_temp_req"),
    #M(0x053d1771 |00 00 00 27 75| Switch to RoomThermo 2
    M(0x053d1289, FB, f.Enable,     "hc1_continuous_pump_operation"),
    M(0x053d1a7a, FB, f.Int32,      "gas_consumption_heating"),
    M(0x053d1a7b, FB, f.Int32,      "gas_consumption_hot_water"),
    M(0x053d1a7c, FB, f.Int32,      "gas_consumption"),
    M(0x053d1ac1, FB, None,         "sitherm_pro_state"), # 00 = off, 0x12: v provozu
    M(0x053d1ac2, FB, None,         "SithermPro_state"), # data[1] is common status value
    M(0x053d2feb, FB, f.Int32,      "hc_op_time"),
    M(0x053d2fec, FB, f.Int32,      "hot_water_op_time"),
    M(0x053d3063, FB, f.Int16,      "burner_water_pressure"),
    M(0x053d3043, FB, f.Int16,      "gas_quality"),
]

messages_by_name = {msg.name: msg for msg in messages}
#messages_by_id = {msg.param & 0xffff: msg for msg in messages}
messages_by_id = {msg.param: msg for msg in messages}
