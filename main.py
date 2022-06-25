import struct
from enum import IntEnum
import pandas as pd
from pathlib import Path

SPEED_CORRECTION_MAGIC_NUMBER = 122
MAGIC_NUMBER = 6 
MAGIC_NUMBER_ROTATION = 360
MAGIC_NUMBER_FF = 256
MAGIC_NUMBER_MILLION = 1000000
LINE_LENGTH = 183

class Field(IntEnum):
    ACC_LAT = 0x11
    ACC_LON = 0x13
    SPEED = 0x17
    TEMP_INTAKE = 0x1d
    TEMP_COOLANT = 0x22
    TEMP_OIL = 0x27
    TEMP_GEARBOX = 0x2c
    TEMP_CLUTCH = 0x31
    THROTTLE = 0x36
    BOOST = 0x3B
    BRAKE = 0x42
    STEERING = 0x47
    RPM = 0x4B
    TORQUE = 0x50
    POWER = 0x58
    GPS_LON = 0x5c
    GPS_LAT = 0x60
    WHEEL_RR = 0x74
    WHEEL_RL = 0x79
    WHEEL_FR = 0x7e
    WHEEL_FL = 0x83
    TEMP_EXTERNAL = 0x93
    GEAR = 0x98
    TIME = 0xA9

def readAccel(value):
    value = value[0]
    sign = -1 if value & 0x8000 == 0 else 1
    return sign * (value & 0x7FFF) / MAGIC_NUMBER_FF

def wheel_speed(read_value):
    return MAGIC_NUMBER_ROTATION * MAGIC_NUMBER_MILLION / read_value if read_value != 0 else 0

def normalize_wheelspeed(value, average): 
    return value / average if average != 0 else 1


run_path = Path("/home/flo/Téléchargements/2022_06_23_17_38_01_49.46685_01.14281_log.run")

with open(run_path, "rb") as in_file: # opening for [r]eading as [b]inary
    data = in_file.read() # if you only wanted to read 512 bytes, do .read(512)

print(len(data))
nb_lines = len(data) // LINE_LENGTH
print(f'nb_lines: {nb_lines}')
max_speed = 0
max_rpm = 0

data_array = []

for f in range(nb_lines):
# for f in range(250, nb_lines):
# for f in range(250, 260):
    run_line = data[f * LINE_LENGTH:(f+1) * LINE_LENGTH]

    acc_lat = readAccel(struct.unpack_from('>H', run_line, Field.ACC_LAT))
    acc_lon = -readAccel(struct.unpack_from('>H', run_line, Field.ACC_LON))
    
    speed = (struct.unpack_from('>i', run_line, Field.SPEED)[0] >> 8) / MAGIC_NUMBER / SPEED_CORRECTION_MAGIC_NUMBER
    
    unpacked = struct.unpack_from('<hxxxhxxxhxxxhxxxhxxxhxxx', run_line, Field.TEMP_INTAKE)
    [temp_intake, temp_coolant, temp_oil, temp_gearbox, temp_clutch, throttle] = [d/10 for d in unpacked]
    
    boost = struct.unpack_from('>h', run_line, Field.BOOST)[0] * 5
    
    brake = struct.unpack_from('<h', run_line, Field.BRAKE)[0] * 0.01
    
    steering = struct.unpack_from('<h', run_line, Field.STEERING)[0] #653
    steering = steering / 10 if steering != -0x8000 else 0
    
    try:
        rpm = (MAGIC_NUMBER * MAGIC_NUMBER_MILLION) / (struct.unpack_from('>i', run_line, Field.RPM)[0] >> 8)
    except ZeroDivisionError:
        rpm = 0
    
    torque = struct.unpack_from('>h', run_line, Field.TORQUE)[0]
    power = struct.unpack_from('>h', run_line, Field.POWER)[0]
    
    [gps_lon, gps_lat] = [d / MAGIC_NUMBER_MILLION for d in struct.unpack_from('>ii', run_line, Field.GPS_LON)]
    
    [wheel_rr, wheel_rl, wheel_fr, wheel_fl] = [wheel_speed(d >> 8) for d in struct.unpack_from('>ixixixix', run_line, Field.WHEEL_RR)]
    avg_wheel = sum([wheel_rr, wheel_rl, wheel_fr, wheel_fl]) / 4
    wheel_rr = normalize_wheelspeed(wheel_rr, avg_wheel)
    wheel_rl = normalize_wheelspeed(wheel_rl, avg_wheel)
    wheel_fr = normalize_wheelspeed(wheel_fr, avg_wheel)
    wheel_fl = normalize_wheelspeed(wheel_fl, avg_wheel)

    temp_external = struct.unpack_from('<h', run_line, Field.TEMP_EXTERNAL)[0] * 0.1
    gear = struct.unpack_from('B', run_line, Field.GEAR)[0]
    time = (struct.unpack_from('>i', run_line, Field.TIME)[0] >> 8) * 0.01

    # print(f'acc_lat: {acc_lat}', end=' ')
    # print(f'acc_lon: {acc_lon}')
    
    data_line = [
        acc_lat,
        acc_lon,
        speed,
        temp_intake,
        temp_coolant,
        temp_oil,
        temp_gearbox,
        temp_clutch,
        throttle,
        boost,
        brake,
        steering,
        rpm,
        torque,
        power,
        gps_lon,
        gps_lat,
        wheel_rr,
        wheel_rl,
        wheel_fr,
        wheel_fl,
        temp_external,
        gear,
        time,
    ]
    data_array.append(data_line)

# exit(0)
columns = [
    'acc_lat',
    'acc_lon',
    'speed',
    'temp_intake',
    'temp_coolant',
    'temp_oil',
    'temp_gearbox',
    'temp_clutch',
    'throttle',
    'boost',
    'brake',
    'steering',
    'rpm',
    'torque',
    'power',
    'gps_lon',
    'gps_lat',
    'wheel_rr',
    'wheel_rl',
    'wheel_fr',
    'wheel_fl',
    'temp_external',
    'gear',
    'time',
]

export_columns = [
    'acc_lat',
    'acc_lon',
    'speed',
    'temp_intake',
    'temp_coolant',
    'temp_oil',
    'temp_gearbox',
    'temp_clutch',
    'throttle',
    'boost',
    'brake',
    'steering',
    'rpm',
    'torque',
    'power',
    'gps_lon',
    'gps_lat',
    'wheel_rr',
    'wheel_rl',
    'wheel_fr',
    'wheel_fl',
    'temp_external',
    'gear',
    'time',
]

df = pd.DataFrame(data_array, columns=columns)
# df.to_csv(run_path.parent / f'{run_path.stem}.csv', columns=export_columns)
# df.to_excel(run_path.parent / f'{run_path.stem}.xlsx', columns=export_columns)
# df.to_excel(run_path.parent / f'{run_path.stem}.xlsx', columns=export_columns)

with open(run_path.parent / f'{run_path.stem}.vbo', 'w') as vbo:
    vbo.write('[column names]\n')
    vbo.write(' '.join(export_columns) + '\n')
    vbo.write('\n')
    vbo.write('[data]\n')
    vbo.write(df.to_string(columns=export_columns, index=False, header=False))
    vbo.write('\n')

for column in columns:
    print(f"Average {column}: {df[column].mean():.2f}")

leftover_bytes = data[LINE_LENGTH * nb_lines:]
# print(leftover_bytes)