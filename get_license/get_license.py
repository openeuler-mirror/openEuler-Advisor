import argparse
import os

from src.license_driver import parse_spec_license, parse_compressed_file_license, get_all_license,\
                                load_config_new, LICENSE_YAML_PATH

COMMAMD_NAME = {
    "from-spec",
    "from-src",
    "from-all"
}

def load_my_args():
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(dest="cmd_name",
                                       help="use sub command to choose get license from spec, compressed file or dir")
    
    spec_parser = subparsers.add_parser("from-spec",
                                        help="get license from spec")
    spec_parser.add_argument("-f", "--file", required=True,
                             help="file path of spec")
    spec_parser.set_defaults(func = parse_spec_license)

    src_parser = subparsers.add_parser("from-src",
                                        help="get license from compressed file")
    src_parser.add_argument("-c", "--compresses", required=True, type=str, nargs="+",
                             help="file path of compressed")
    src_parser.add_argument("-e", "--extract_dir", default="/tmp/get_licenses/pkg_src",
                             help="file dir of extract")
    src_parser.set_defaults(func = parse_compressed_file_license)

    all_parser = subparsers.add_parser("from-all",
                                        help="get license from compressed file")
    all_parser.add_argument("-d", "--work_dir", required=True,
                             help="file path of parsed dir")
    all_parser.add_argument("-e", "--extract_dir", default="/tmp/get_licenses/pkg_src",
                             help="file dir of extract")
    all_parser.set_defaults(func = get_all_license)

    return parser.parse_args()


if __name__ == "__main__":
    args = load_my_args()

    result = {}
    spec_lic = {}
    src_lic = {}
    pl = load_config_new(LICENSE_YAML_PATH)
    if not args.cmd_name or not args.cmd_name in COMMAMD_NAME:
        print("not find cmd")
    else:
        if args.cmd_name == "from-all":
            spec_lic, src_lic = args.func(args.work_dir, args.extract_dir, pl)
        elif args.cmd_name == "from-src":
            src_lic = args.func(args.compresses, args.extract_dir, pl)
        elif args.cmd_name == "from-spec":
            spec_lic = args.func(args.file, pl)
    result["spec_license"] = spec_lic
    result["src_license"] = src_lic

    print(result) 
    