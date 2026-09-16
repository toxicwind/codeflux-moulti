#!/usr/bin/env python3
"""Apply the codeflux `moulti stream` subcommand hook to src/moulti/cli.py.

Additive only: inserts a `stream()` wrapper before add_main_commands and a
`stream` subparser before the `set` command. Idempotent.
"""
import sys

PATH = "/home/toxic/sovereign/codeflux/forks/moulti/src/moulti/cli.py"

WRAPPER_ANCHOR = "def add_main_commands(subparsers: _SubParsersAction) -> None:\n"
WRAPPER_INSERT = (
    "def stream(args: dict) -> None:\n"
    "\tfrom .streaming import stream as real_stream # pylint: disable=import-outside-toplevel\n"
    "\treal_stream(args)\n"
    "\n"
    "\n"
)

PARSER_ANCHOR = "\t# moulti set\n\tset_parser = subparsers.add_parser('set', help='set Moulti options')\n"
PARSER_INSERT = (
    "\t# moulti stream (codeflux improvement: ingest JSONL patch events from stdin)\n"
    "\tstream_parser = subparsers.add_parser('stream', help='ingest JSONL patch events from stdin into steps')\n"
    "\tstream_parser.set_defaults(func=stream)\n"
    "\tstream_parser.add_argument('--dry-run', action='store_true', default=False, help='print the moulti commands instead of executing them')\n"
    "\n"
    "\n"
)


def main() -> None:
    src = open(PATH).read()
    changed = False
    if "def stream(args: dict) -> None:" not in src:
        if WRAPPER_ANCHOR not in src:
            sys.exit("ANCHOR MISSING: add_main_commands")
        src = src.replace(WRAPPER_ANCHOR, WRAPPER_INSERT + WRAPPER_ANCHOR, 1)
        changed = True
    if "stream_parser = subparsers.add_parser('stream'" not in src:
        if PARSER_ANCHOR not in src:
            sys.exit("ANCHOR MISSING: moulti set parser")
        src = src.replace(PARSER_ANCHOR, PARSER_INSERT + PARSER_ANCHOR, 1)
        changed = True
    if changed:
        open(PATH, "w").write(src)
        print("cli.py hooked: moulti stream subcommand added")
    else:
        print("cli.py already hooked; nothing to do")


if __name__ == "__main__":
    main()
