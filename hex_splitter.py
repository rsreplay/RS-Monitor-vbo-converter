import struct
import sys
from pathlib import Path

import pandas as pd

from vars import *

run_path = Path(sys.argv[1])
# run_path = Path("./Acquisitions/2022_06_25_16_22_20_49.51682_01.13814_log.run")

with open(run_path, "rb") as in_file:  # opening for [r]eading as [b]inary
    data = in_file.read()  # if you only wanted to read 512 bytes, do .read(512)

print(len(data))
nb_lines = len(data) // LINE_LENGTH
print(f'nb_lines: {nb_lines}')
max_speed = 0
max_rpm = 0

data_array = []
fmt = ''.join('B' * LINE_LENGTH)

for f in range(nb_lines):
# for f in range(50):
# for f in range(nb_lines - 10, nb_lines):
    # for f in range(250, 260):
    run_line = data[f * LINE_LENGTH:(f + 1) * LINE_LENGTH]
    data_line = struct.unpack_from(fmt, run_line)

    data_array.append(data_line)

columns = [hex(c) for c in range(LINE_LENGTH)]

df = pd.DataFrame(data_array, columns=columns)

# for column in columns:
#     print(f"Average {column}: {df[column].mean():.2f}")


df.to_csv(run_path.parent / f'{run_path.stem}-bytes.csv', columns=columns, index=False)  # , quoting=csv.QUOTE_NONNUMERIC )
df.to_excel(run_path.parent / f'{run_path.stem}-bytes.xlsx', columns=columns, index=False)
# df.to_excel(run_path.parent / f'{run_path.stem}.xlsx', columns=export_columns)
