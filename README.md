# RS Monitor vbo converter

Convert the .run files from the RS Monitor acquisition to .vbo files compatible with [Racelogic Circuit Tools](https://www.vboxmotorsport.co.uk/index.php/en/circuit-tools)

## Installation
- Setup a [Python](https://www.python.org/) environment
- Install Pandas `pip install pandas`
- Download and extract this repository

## Usage
Call main.py with the full path to one or mode .run files. The .vbo files will be written to the same folder.

Example:
```shell
python main.py "C:/Users/flolbr/Downloads/2022_06_24_17_12_17_49.46683_01.14284_log.run" "2022_06_23_17_38_01_49.46685_01.14281_log.run"
```

## Other tools

### Hex Splitter

Exports a run file as a couple of CSV/Excel files for deeper inspection.

Example:
```shell
python hex_splitter.py "C:/Users/flolbr/Downloads/2022_06_24_17_12_17_49.46683_01.14284_log.run"
```