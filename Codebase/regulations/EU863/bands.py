from Codebase.regulations.band import Band
from Codebase.regulations.duty_cycles import DutyCycles

BAND_K = Band(
    name="K",
    start=863.000,
    end=865.000,
    erp=25,
    duty_cycle=DutyCycles.DC_0_1,
    note=None
)

BAND_L = Band(
    name="L",
    start=865.000,
    end=868.000,
    erp=25,
    duty_cycle=DutyCycles.DC_1,
    note=None
)

BAND_M = Band(
    name="M",
    start=868.000,
    end=868.600,
    erp=25,
    duty_cycle=DutyCycles.DC_1,
    note=None
)

BAND_N = Band(
    name="N",
    start=868.700,
    end=869.200,
    erp=25,
    duty_cycle=DutyCycles.DC_0_1,
    note=None
)

BAND_O = Band(
    name="O",
    start=869.400,
    end=869.650,
    erp=500,
    duty_cycle=DutyCycles.DC_10,
    note=None
)

BAND_P = Band(
    name="P",
    start=869.700,
    end=870.000,
    erp=5,
    duty_cycle=DutyCycles.DC_100,
    note="Voice applications allowed with advanced mitigation technique. " \
    "Other audio and video applications are excluded."
)

BAND_Q = Band(
    name="Q",
    start=869.700,
    end=870.000,
    erp=25,
    duty_cycle=DutyCycles.DC_1,
    note=None
)
