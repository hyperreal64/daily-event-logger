# daily-event-logger

This is a little utility I use for logging my daily activities and events. It is written in Python.

## Install

```bash
python3 -m pip install daily-event-logger
```

## Usage

To change the directory where elogs are stored, set a shell environment variable ELOG_DIR. To make this change permament, set the following in your shell configuration:

```bash
export ELOG_DIR="/path/to/elog/dir"
```

Otherwise, the default elog directory will be `~/elogs`.

To get started, add your first elog entry! This will create a JSON file under your elog directory for the day and ensure the elog directory exists. E.g.:

```bash
elog add -m "Started new elog. Yay!"
```

```bash
usage: elog [-h] [-v] {add,edit,rm,ls,lsfiles,search} ...

positional arguments:
  {add,edit,rm,ls,lsfiles,search}

options:
  -h, --help            show this help message and exit
  -v, --version         Print version information
```

### Example list output
![screenshot.png](/screenshot.png)

