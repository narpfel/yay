import argparse
from importlib.machinery import SourceFileLoader
import sys


def import_yay_file(yay_filename):
    return SourceFileLoader("main", yay_filename).load_module()


def get_main_class(namespace, class_name):
    return getattr(namespace, class_name)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="yay",
        description="Yay assembler.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("yay_file", help="the file that will be assembled")
    parser.add_argument(
        "--main_class",
        help="the class that contains the main program",
        default="Main"
    )

    output_types = parser.add_mutually_exclusive_group()
    output_types.add_argument(
        "-o", "--outfile",
        help="write assembled program to this location",
    )
    output_types.add_argument(
        "-r", "--print-raw",
        help="print raw bytes to stdout instead of printing the repr of the"
            " binary",
        action="store_true"
    )

    parser.add_argument(
        "-f", "--format",
        help="output format of the assembled program",
        default="ihex"
    )

    args = parser.parse_args(argv)

    main_class = get_main_class(import_yay_file(args.yay_file), args.main_class)
    program = main_class()
    output = getattr(program, "to_{}".format(args.format))()

    if args.outfile:
        # TODO: Is always encoding `str`s (currently only returned by
        # `to_ihex`) always right?
        if isinstance(output, str):
            output = output.encode()
        with open(args.outfile, "wb") as outfile:
            outfile.write(output)
    elif args.print_raw:
        sys.stdout.buffer.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
