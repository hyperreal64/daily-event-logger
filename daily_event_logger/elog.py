"""elog - daily event logger."""

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import jsonschema
from jsonschema import validate
from rich import box
from rich.console import Console
from rich.table import Table
from rich.traceback import install

install(show_locals=True)

VERSION = "0.1.4"

default_date = dt.date.today().strftime("%Y-%m-%d")
ELOG_DIR = os.getenv("ELOG_DIR")
if ELOG_DIR is None:
    elog_dir = Path("~/elogs").expanduser()
else:
    elog_dir = Path(ELOG_DIR)


def elog_init(filename):
    """Initialize elog file and directory, if necessary.

    elog_dir is taken from the current shell's ELOG_DIR environment variable, or else it defaults to
    ~/elogs.
    """
    elog_file = elog_dir.joinpath(filename).with_suffix(".json")

    elog_dir.mkdir(exist_ok=True)
    elog_file.touch()

    json_array = []

    with open(elog_file, "w") as ef:
        json.dump(json_array, ef)


def elog_list(args):
    """List elog entries.

    Lists elog entries for provided timestamp range and/or elog file
    """
    if args.file:
        selected_elog_file = elog_dir.joinpath(args.file)
    else:
        selected_elog_file = elog_dir.joinpath(default_date + "_elog").with_suffix(
            ".json"
        )

    if not selected_elog_file.exists():
        exit("elog file %s not found. Are you sure it exists?" % selected_elog_file)

    if not args.start:
        ts_from = selected_elog_file.stem[:10] + " 00:00:00"
    else:
        dt.datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
        ts_from = args.start

    if not args.end:
        ts_to = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        dt.datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")
        ts_to = args.end

    with open(selected_elog_file, "r") as ef:
        json_data = json.load(ef)

    table = Table(style="green", header_style="bold", box=box.ROUNDED)
    table.add_column("Index", justify="right", style="white")
    table.add_column("Timestamp", justify="left", style="red")
    table.add_column("Message", justify="left")

    for i in range(len(json_data)):
        if json_data[i]["timestamp"] > ts_from and json_data[i]["timestamp"] < ts_to:
            table.add_row(str(i), json_data[i]["timestamp"], json_data[i]["message"])

    console = Console(color_system="256")
    console.print(table)


def elog_list_files(args):
    """List all elog files.

    Lists all elog files currently present in elog directory.
    """
    for file in sorted(elog_dir.iterdir()):
        if file.is_file():
            if args.absolute:
                print(file)
            else:
                print(file.name)


def elog_search(args):
    """Search for a string.

    Searches all elog files and prints found matches.
    """
    found_entries = list()
    elog_list = [file.name for file in elog_dir.iterdir()]

    console = Console()

    for file in elog_list:
        with open(elog_dir.joinpath(file), "r") as ef:
            json_data = json.load(ef)
            for entry in json_data:
                if args.word in entry["message"]:
                    found_entries.append(entry)

    if found_entries:
        for entry in found_entries:
            console.print(
                "[bold green]{0}[/bold green] {1}".format(
                    entry["timestamp"], entry["message"]
                )
            )
    else:
        console.print(
            "[bold yellow]{0}[/bold yellow] was not found in any of the elog files".format(
                args.word
            )
        )


def elog_sort(file):
    """Sort elog entries.

    Entries are sorted by provided timestamp.
    """
    with open(file, "r") as ef:
        json_data = json.load(ef)
        json_data.sort(
            key=lambda x: time.mktime(
                time.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S")
            )
        )

    with open(file, "w") as ef:
        json.dump(json_data, ef, indent=4)


def validate_json(file):
    """Validate JSON data.

    Call jsonschema.validate on `file`.
    """
    elog_schema = {
        "type": "array",
        "properties": {
            "timestamp": {"type": "string"},
            "message": {"type": "string"},
        },
    }

    with open(file, "r") as ef:
        json_data = json.load(ef)

    try:
        validate(instance=json_data, schema=elog_schema)
    except jsonschema.ValidationError as err:
        print("Invalid JSON detected on %s" % file)
        print(err)


def elog_append(args):
    """
    Append a new elog entry to the elog file.

    Use elog file indicated by provided timestamp, or else use the elog file for current day.
    """
    if not args.timestamp:
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        dt.datetime.strptime(args.timestamp, "%Y-%m-%d %H:%M:%S")
        ts = args.timestamp

    elog_filename = ts[:10] + "_elog"
    elog_file = elog_dir.joinpath(elog_filename).with_suffix(".json")

    if not elog_file.exists():
        elog_init(elog_file)

    entry = {"timestamp": ts, "message": args.message}

    with open(elog_file, "r+") as ef:
        json_data = json.load(ef)
        json_data.append(entry)
        ef.seek(0)
        json.dump(json_data, ef, indent=4)

    elog_sort(elog_file)
    validate_json(elog_file)


def elog_edit(args):
    """Edit elog entry at provided index argument."""
    if args.file:
        elog_file = elog_dir.joinpath(args.file)
    else:
        elog_file = elog_dir.joinpath(default_date + "_elog").with_suffix(".json")

    if not elog_file.exists():
        exit("elog file not found. Please run 'elog append' to start a new elog file.")

    with open(elog_file, "r+") as ef:
        json_data = json.load(ef)
        json_data[args.index]["message"] = args.message
        ef.seek(0)
        json.dump(json_data, ef, indent=4)

    validate_json(elog_file)


def elog_remove(args):
    """Remove an elog entry at provided index argument."""
    if args.file:
        elog_file = elog_dir.joinpath(args.file)
    else:
        elog_file = elog_dir.joinpath(default_date + "_elog").with_suffix(".json")

    if not elog_file.exists():
        exit("elog file not found. Please run 'elog append' to start a new elog file.")

    with open(elog_file, "r") as ef:
        json_data = json.load(ef)
        json_data.pop(args.index)

    with open(elog_file, "w") as ef:
        json.dump(json_data, ef, indent=4)

    validate_json(elog_file)


parser = argparse.ArgumentParser(prog="elog")
parser.add_argument(
    "-v",
    "--version",
    action="version",
    version="%(prog)s {}".format(VERSION),
    help="Print version information",
)
subparsers = parser.add_subparsers()

add_parser = subparsers.add_parser("add", description="Add an elog entry")
add_parser.add_argument(
    "-t",
    "--timestamp",
    required=False,
    type=str,
    action="store",
    help="Timestamp for elog entry: str",
)
add_parser.add_argument(
    "-m",
    "--message",
    required=True,
    type=str,
    action="store",
    help="Message for elog entry: str",
)
add_parser.set_defaults(func=elog_append)

edit_parser = subparsers.add_parser("edit", description="Edit an elog entry")
edit_parser.add_argument(
    "-i",
    "--index",
    required=True,
    type=int,
    action="store",
    help="Index of elog entry: int",
)
edit_parser.add_argument(
    "-m",
    "--message",
    required=True,
    type=str,
    action="store",
    help="New message for elog entry: str",
)
edit_parser.add_argument(
    "-f",
    "--file",
    required=False,
    type=str,
    action="store",
    help="elog file to edit. Ex: 2022-10-02_elog.json",
)
edit_parser.set_defaults(func=elog_edit)

rm_parser = subparsers.add_parser("rm", description="Remove an elog entry")
rm_parser.add_argument(
    "-i",
    "--index",
    required=True,
    type=int,
    action="store",
    help="Index of elog entry: int",
)
rm_parser.add_argument(
    "-f",
    "--file",
    required=False,
    type=str,
    action="store",
    help="elog file to remove from. Ex: 2022-10-02_elog.json",
)
rm_parser.set_defaults(func=elog_remove)

ls_parser = subparsers.add_parser("ls", description="List elog entries")
ls_parser.add_argument(
    "-s",
    "--start",
    metavar="TIMESTAMP",
    required=False,
    type=str,
    action="store",
    help="From timestamp: str. Default is today at 00:00:00. Ex. 2022-09-28 13:45:00",
)
ls_parser.add_argument(
    "-e",
    "--end",
    metavar="TIMESTAMP",
    required=False,
    type=str,
    action="store",
    help="To timestamp: str. Default is today at now. Ex. 2022-09-28 21:00:00",
)
ls_parser.add_argument(
    "-f",
    "--file",
    required=False,
    type=str,
    action="store",
    help="elog file to view. Ex: 2022-10-02_elog.json",
)
ls_parser.set_defaults(func=elog_list)

ls_files_parser = subparsers.add_parser("lsfiles", description="List all elog files")
ls_files_parser.add_argument(
    "-a",
    "--absolute",
    required=False,
    action="store_true",
    help="List the absolute paths of the elog files",
)
ls_files_parser.set_defaults(func=elog_list_files)

search_parser = subparsers.add_parser(
    "search", description="Search for keywords in elog files"
)
search_parser.add_argument(
    "-w", "--word", required=True, type=str, action="store", help="Word to search for"
)
search_parser.set_defaults(func=elog_search)


def main():
    """Parse command line arguments and run desired function.

    Checks if the number of arguments provided at the command line is less than the required number,
    and if so, it prints the usage message.
    """
    if len(sys.argv) < 2:
        parser.print_usage()
    else:
        args = parser.parse_args()
        args.func(args)
