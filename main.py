from __future__ import annotations

import re
import struct
import sys
from datetime import timedelta, datetime
from math import floor, log, ceil, log10
from pathlib import Path
from time import sleep

import pandas as pd
from PyQt6 import uic
from PyQt6.QtCore import QThreadPool, Qt
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QCloseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolButton, QFileDialog, QLabel, QCheckBox

from Worker import Worker
from bundle import bundle_dir
from rsm_config import config
from runtime import runtime
from vars import *

columns = [
    'latacc',
    'longacc',
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
    'longitude',
    'latitude',
    'wheel_rr',
    'wheel_rl',
    'wheel_fr',
    'wheel_fl',
    'temp_external',
    'gear',
    'time',
]
column_names = {
    'latacc': 'latacc',
    'longacc': 'longacc',
    'speed': 'velocity kmh',
    'velocity': 'velocity kmh',
    'temp_intake': 'temp_intake',
    'temp_coolant': 'temp_coolant',
    'temp_oil': 'temp_oil',
    'temp_gearbox': 'temp_gearbox',
    'temp_clutch': 'temp_clutch',
    'throttle': 'throttle',
    'boost': 'boost',
    'brake': 'brake',
    'steering': 'steering',
    'rpm': 'rpm',
    'torque': 'torque',
    'power': 'power',
    'long': 'longitude',
    'lat': 'latitude',
    'wheel_rr': 'wheel_rr',
    'wheel_rl': 'wheel_rl',
    'wheel_fr': 'wheel_fr',
    'wheel_fl': 'wheel_fl',
    'temp_external': 'temp_external',
    'gear': 'gear',
    'time': 'time',
    'sats': 'satellites',
    'event1': 'Event 1 time',
    'heading': 'heading',
    'height': 'height',
}


def read_accel(value):
    value = value[0]
    sign = -1 if value & 0x8000 == 0 else 1
    return sign * (value & 0x7FFF) / MAGIC_NUMBER_FF


def wheel_speed(read_value):
    return MAGIC_NUMBER_ROTATION * MAGIC_NUMBER_MILLION / read_value if read_value != 0 else 0


def normalize_wheelspeed(value, average):
    return value / average if average != 0 else 1


def lat_lon_to_dsm(lat_or_lon):
    # return lat_or_lon
    value = abs(lat_or_lon)
    val_deg = floor(value)
    val_min = floor((value - val_deg) * 60)
    val_sec = (value - val_deg - val_min / 60) * 3600
    # val_sec = round((value - val_deg - val_min / 60) * 3600 * 1000) / 1000

    result = "-" if (lat_or_lon < 0) else "+"
    result += str(val_deg * 60 + val_min)
    result += "."
    result += str(val_sec)

    if int(val_sec) > 0:
        val_sec2 = val_sec / 10 ** ceil(log10(val_sec))
    else:
        val_sec2 = val_sec
    # print(result)

    integer_part = val_deg * 60 + val_min
    result3 = integer_part + val_sec2

    result2 = (-1 if (lat_or_lon < 0) else 1) * val_deg * 60 + val_min + (val_sec / pow(10, (int(log(val_sec)) - 1)))

    # return result3
    return lat_or_lon * 60


def convert(run_path, export_options=None):
    export_columns = [
        'time',
        # 'latacc',
        # 'longacc',
        'latitude',
        'longitude',
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
        'wheel_rr',
        'wheel_rl',
        'wheel_fr',
        'wheel_fl',
        'temp_external',
        'gear',
    ]

    with open(run_path, "rb") as in_file:  # opening for [r]eading as [b]inary
        data = in_file.read()  # if you only wanted to read 512 bytes, do .read(512)
    print(len(data))
    nb_lines = len(data) // LINE_LENGTH
    print(f'nb_lines: {nb_lines}')
    data_array = []
    for f in range(nb_lines):
        # for f in range(50):
        # for f in range(nb_lines - 10, nb_lines):
        # for f in range(250, 260):
        run_line = data[f * LINE_LENGTH:(f + 1) * LINE_LENGTH]

        latacc = read_accel(struct.unpack_from('>H', run_line, Field.ACC_LAT))
        longacc = -read_accel(struct.unpack_from('>H', run_line, Field.ACC_LON))

        speed = (struct.unpack_from('>i', run_line, Field.SPEED)[0] >> 8) / MAGIC_NUMBER / SPEED_CORRECTION_MAGIC_NUMBER

        unpacked = struct.unpack_from('<hxxxhxxxhxxxhxxxhxxxhxxx', run_line, Field.TEMP_INTAKE)
        [temp_intake, temp_coolant, temp_oil, temp_gearbox, temp_clutch, throttle] = [d / 10 for d in unpacked]

        boost = struct.unpack_from('>h', run_line, Field.BOOST)[0] * 5

        brake = struct.unpack_from('<h', run_line, Field.BRAKE)[0] * 0.01

        steering = struct.unpack_from('<h', run_line, Field.STEERING)[0]  # 653
        steering = steering / 10 if steering != -0x8000 else 0

        try:
            rpm = (MAGIC_NUMBER * MAGIC_NUMBER_MILLION) / (struct.unpack_from('>i', run_line, Field.RPM)[0] >> 8)
        except ZeroDivisionError:
            rpm = 0

        torque = struct.unpack_from('>h', run_line, Field.TORQUE)[0]
        power = struct.unpack_from('>h', run_line, Field.POWER)[0]

        [longitude, latitude] = [lat_lon_to_dsm(d / 10_000_000) for d in
                                 struct.unpack_from('>ii', run_line, Field.LONGITUDE)]

        [wheel_rr, wheel_rl, wheel_fr, wheel_fl] = [wheel_speed(d >> 8) for d in
                                                    struct.unpack_from('>ixixixix', run_line, Field.WHEEL_RR)]
        avg_wheel = sum([wheel_rr, wheel_rl, wheel_fr, wheel_fl]) / 4
        wheel_rr = normalize_wheelspeed(wheel_rr, avg_wheel)
        wheel_rl = normalize_wheelspeed(wheel_rl, avg_wheel)
        wheel_fr = normalize_wheelspeed(wheel_fr, avg_wheel)
        wheel_fl = normalize_wheelspeed(wheel_fl, avg_wheel)

        temp_external = struct.unpack_from('<h', run_line, Field.TEMP_EXTERNAL)[0] * 0.1
        gear = struct.unpack_from('B', run_line, Field.GEAR)[0]
        time = (struct.unpack_from('>i', run_line, Field.TIME)[0] >> 8) * 0.01

        # print(f'latacc: {latacc}', end=' ')
        # print(f'longacc: {longacc}')

        data_line = [
            latacc,
            longacc,
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
            longitude,
            latitude,
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

    df = pd.DataFrame(data_array, columns=columns)
    # for column in columns:
    #     print(f"Average {column}: {df[column].mean():.2f}")
    if export_options is not None and export_options['exportCsv']:
        df.to_csv(run_path.parent / f'{run_path.stem}.csv', columns=export_columns,
                  index=False)  # , quoting=csv.QUOTE_NONNUMERIC )
    # df.to_excel(run_path.parent / f'{run_path.stem}.xlsx', columns=export_columns)
    # df.to_excel(run_path.parent / f'{run_path.stem}.xlsx', columns=export_columns)
    # df['time'] = df['time'] * 1000
    export_columns.insert(0, 'sats')
    df['sats'] = "%03d" % 5
    # export_columns.append('event1')
    # df['event1'] = '%04d' % 0
    export_columns.append('heading')
    df['heading'] = '%03.2f' % 0
    export_columns.append('height')
    df['height'] = '%+05.2f' % 0
    df["latitude"] = df["latitude"].apply(lambda v: "%+012.5f" % v)
    df["longitude"] = df["longitude"].apply(lambda v: "%+012.5f" % -v)
    df["speed"] = df["speed"].apply(lambda v: "%07.3f" % v)

    def _seconds_to_hms(secs):
        int_secs = int(secs)
        # Get relative time in seconds (without the fractional part).
        rel_time = (datetime.min + timedelta(seconds=int_secs)).time()
        # Round the fractional part to milliseconds.
        # int_msecs = int((secs - int_secs).quantize(
        #     # Always round halves up.
        #     Decimal("0.01"), rounding=ROUND_HALF_UP
        # ).shift(2))
        int_msecs = int((secs - int_secs) * 100)
        return "%s.%02d" % (rel_time.strftime("%H%M%S"), int_msecs)

    df['time'] = df['time'].apply(_seconds_to_hms)
    # new_column_names = {'speed': 'velocity kmh'}
    new_column_names = {
        'longitude': 'long',
        'latitude': 'lat',
        'speed': 'velocity'
    }

    for i, c in enumerate(export_columns):
        for nc in new_column_names.keys():
            if c == nc:
                export_columns[i] = new_column_names[nc]

    df.rename(columns=new_column_names, inplace=True)

    if export_options is not None and export_options['exportVbo']:
        with open(run_path.parent / f'{run_path.stem}.vbo', 'w') as vbo:
            vbo.write(datetime.now().strftime("File created on %d/%m/%Y at %I:%M:%S %p"))
            vbo.write('\n')
            vbo.write('\n')

            vbo.write('[header]\n')
            vbo.write('\n'.join([column_names[c] for c in export_columns]) + '\n')
            vbo.write('\n')

            vbo.write('[comments]\n')
            # # vbo.write('(c) 2001 2003 Racelogic\n')
            # # vbo.write('VBox II Version 4.5a\n')
            # # vbo.write('GPS : SSX2g\n')
            # # vbo.write('Serial Number : 005201\n')
            # # vbo.write('CF Version 2.1d\n')
            vbo.write('Log Rate (Hz) : 10.00\n')
            vbo.write('name Abbeville\n')
            vbo.write('\n')

            vbo.write('[column names]\n')
            vbo.write(' '.join(export_columns) + '\n')
            vbo.write('\n')

            vbo.write('[data]\n')
            data = df.to_string(columns=export_columns, index=False, header=False)
            vbo.write(re.sub(r' +', ' ', data))
            vbo.write('\n')
    leftover_bytes = data[LINE_LENGTH * nb_lines:]
    # print(leftover_bytes)


def cli_app():
    if len(sys.argv) > 1:
        for run_path in sys.argv[1:]:
            print(f'Converting {run_path}...')
            convert(Path(run_path))
    else:
        run_path = Path("./Acquisitions/2022_06_23_17_38_01_49.46685_01.14281_log.run")
        convert(run_path)


def get_path_from_event(event):
    paths = event.mimeData().text().split('\n')
    return list(map(lambda p: p.removeprefix('file:///'), list(filter(None, paths))))


def check_state(status):
    return Qt.CheckState.Checked if status else Qt.CheckState.Unchecked


class MainWindow(QMainWindow):
    # Buttons
    fileBrowserToolButton: QToolButton
    convertToolButton: QToolButton
    statusLabel: QLabel
    exportVboCheckBox: QCheckBox
    exportCsvCheckBox: QCheckBox
    exportRawCsvCheckBox: QCheckBox
    exportRawXslxCheckBox: QCheckBox

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.program_workers = 0
        self.selected_files = []

        # Load the UI Page
        uic.loadUi(bundle_dir + 'ui/mainwindow.ui', self)

        # Setup the bindings
        self.fileBrowserToolButton.clicked.connect(self.open_file_browser)
        self.convertToolButton.clicked.connect(self.run_conversion)

        self.setWindowTitle(f'{self.windowTitle()} {runtime.version}')
        self.setWindowIcon(QIcon(bundle_dir + '/img/icon.png'))

        # Fill the config elements
        def _load_config_items():
            self.exportVboCheckBox.setCheckState(check_state(config['checkboxes']['exportVbo']))
            self.exportCsvCheckBox.setCheckState(check_state(config['checkboxes']['exportCsv']))
            self.exportRawCsvCheckBox.setCheckState(check_state(config['checkboxes']['exportRawCsv']))
            self.exportRawXslxCheckBox.setCheckState(check_state(config['checkboxes']['exportRawXslx']))

        self.exportVboCheckBox.clicked.connect(lambda s: config['checkboxes'].__setitem__('exportVbo', s))
        self.exportCsvCheckBox.clicked.connect(lambda s: config['checkboxes'].__setitem__('exportCsv', s))
        self.exportRawCsvCheckBox.clicked.connect(lambda s: config['checkboxes'].__setitem__('exportRawCsv', s))
        self.exportRawXslxCheckBox.clicked.connect(lambda s: config['checkboxes'].__setitem__('exportRawXslx', s))

        _load_config_items()

    def closeEvent(self, event: QCloseEvent) -> None:
        config.save()

    def dragEnterEvent(self, event: QDragEnterEvent):
        paths = get_path_from_event(event)
        for path in paths:
            if not path.endswith('.run'):
                event.ignore()
                return
        event.setDropAction(Qt.DropAction.LinkAction)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        event.accept()
        paths = get_path_from_event(event)
        print(paths)
        for path in paths:
            self.selected_files.append(path)
        self.update_selected_files()

    def open_file_browser(self):
        # Open the file browser
        (self.selected_files, _) = QFileDialog.getOpenFileNames(self, 'Open file', config['lastDir'],
                                                                f"RS Monitor Run files (*.run)")

        self.update_selected_files()

    def update_selected_files(self):
        file_num = len(self.selected_files)
        # Set the status bar text
        if file_num == 0:
            text = 'No file selected'
        elif file_num == 1:
            text = '1 file selected'
        else:
            text = f'{file_num} files selected'
        self.statusLabel.setText(text)
        # Save the last opened path if at least one file has been selected
        if file_num:
            self.convertToolButton.setEnabled(True)
            config['lastDir'] = str(Path(self.selected_files[0]).parent.absolute())
            config.save()

    def program_done(self):
        self.program_workers -= 1
        if self.program_workers == 0:
            self.convertToolButton.setDisabled(False)
            self.statusLabel.setText(f'Done.')
            print('Done.')

    def run_conversion(self):
        def test(run_path, *args, **kwargs):
            workers_ = self.program_workers * 3
            print('Sleeping for %d seconds...\n' % workers_)
            sleep(workers_)
            return run_path

        config.save()

        for run_path in self.selected_files:
            self.convertToolButton.setDisabled(True)
            print(f'Converting {run_path}...')
            self.statusLabel.setText(f'Converting {run_path}...')
            worker = Worker(convert, Path(run_path), config['checkboxes'])
            worker.signals.WrkRsult.connect(lambda p: print(f'Worker Done: {p}'))
            worker.signals.WrksDone.connect(self.program_done)
            self.program_workers += 1
            QThreadPool.globalInstance().start(worker)


def gui_app():
    runtime.gui = True
    app = QApplication(sys.argv)
    window = MainWindow()
    runtime.main_window = window
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cli_app()
    else:
        gui_app()
