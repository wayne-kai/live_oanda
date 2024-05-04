from enum import IntEnum

class Status(IntEnum):
    Active = 1
    Inactive = 2
    Stop = 3

    Unknown = 0

class Models(IntEnum): 
    OneMin = 1
    FiveMin = 2
    FifteenMin = 3
    OneHour = 4

    Unknown = 0
