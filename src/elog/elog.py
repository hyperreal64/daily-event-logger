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

VERSION = "0.0.8"

default_date = dt.date.today().strftime("%Y-%m-%d")
ELOG_DIR = os.getenv("ELOG_DIR")
if ELOG_DIR is None:
    elog_dir = Path("~/elogs").expanduser()
else:
    elog_dir = Path(ELOG_DIR)
elog_file = elog_dir.joinpath(default_date + "_elog").with_suffix(".json")


def elog_init():
    elog_file = elog_dir.joinpath(default_date + "_elog").with_suffix(".json")

    elog_dir.mkdir(exist_ok=True)
    elog_file.touch()

    json_array = []

    with open(elog_file, "w") as ef:
        json.dump(json_array, ef)


def elog_list(args):
    if args.file:
        selected_elog_file = elog_dir.joinpath(args.file)
    else:
        selected_elog_file = elog_file

    if not selected_elog_file.exists():
        exit("elog file %s not found. Are you sure it exists?" % selected_elog_file)

    if not args.start:
        ts_from = default_date + " 00:00:00"
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

    table = Table(title=default_date, box=box.ROUNDED)
    table.add_column("Index", justify="right", style="magenta")
    table.add_column("Timestamp", justify="left", style="cyan")
    table.add_column("Message", justify="left")

    for i in range(len(json_data)):
        if json_data[i]["timestamp"] > ts_from and json_data[i]["timestamp"] < ts_to:
            table.add_row(str(i), json_data[i]["timestamp"], json_data[i]["message"])

    console = Console()
    console.print(table)


def elog_list_files(args):
    for file in elog_dir.iterdir():
        if file.is_file():
            if args.absolute:
                print(file)
            else:
                print(file.name)


def elog_search(args):
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
    if not elog_file.exists():
        elog_init()

    if not args.timestamp:
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        dt.datetime.strptime(args.timestamp, "%Y-%m-%d %H:%M:%S")
        ts = args.timestamp

    entry = {"timestamp": ts, "message": args.message}

    with open(elog_file, "r+") as ef:
        json_data = json.load(ef)
        json_data.append(entry)
        ef.seek(0)
        json.dump(json_data, ef, indent=4)

    elog_sort(elog_file)
    validate_json(elog_file)


def elog_edit(args):
    if not elog_file.exists():
        exit("elog file not found. Please run 'elog append' to start a new elog file.")

    with open(elog_file, "r+") as ef:
        json_data = json.load(ef)
        json_data[args.index]["message"] = args.message
        ef.seek(0)
        json.dump(json_data, ef, indent=4)

    validate_json(elog_file)


def elog_remove(args):
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
rm_parser.set_defaults(func=elog_remove)

ls_parser = subparsers.add_parser("ls", description="List elog entries")
ls_parser.add_argument(
    "-s",
    "--start",
    metavar="timestamp",
    required=False,
    type=str,
    action="store",
    help="From timestamp: str. Default is today at 00:00:00. Ex. 2022-09-28 13:45:00",
)
ls_parser.add_argument(
    "-e",
    "--end",
    metavar="timestamp",
    required=False,
    type=str,
    action="store",
    help="To timestamp: str. Default is today at now. Ex. 2022-09-28 21:00:00",
)
ls_parser.add_argument(
    "-f",
    "--file",
    metavar="elog file",
    required=False,
    type=str,
    action="store",
    help="elog file to view",
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
    "-w",
    "--word",
    metavar="<word>",
    required=True,
    type=str,
    action="store",
    help="Word to search for",
)
search_parser.set_defaults(func=elog_search)


def main():
    if len(sys.argv) < 2:
        parser.print_usage()
    else:
        args = parser.parse_args()
        args.func(args)
