#!/usr/bin/python3
"""
This is a command line tool for adding new repo
"""

import argparse
import yaml
import sys


if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-r", "--repo", help="YAML file for repositories", type=str, required=True)
    par.add_argument("-i", "--sigs", help="YAML file for sigs", type=str, required=True)
    par.add_argument("-s", "--sig", help="Sig manage this repo", type=str, required=True)
    par.add_argument("-n", "--name", help="Name for new repo", type=str, required=True)
    par.add_argument("-d", "--desc", help="Description for new repo", type=str, required=True)
    par.add_argument("-u", "--upstream", help="Upstream for new repo", type=str, required=True)

    args = par.parse_args()

    f = open(args.sigs)
    sigs = yaml.load(f.read(), Loader=yaml.Loader)
    if not sigs:
        print("Failed to load {file}".format(file=args.sigs))
        sys.exit(1)
    f.close()

    f = open(args.repo)
    repo = yaml.load(f.read(), Loader=yaml.Loader)
    if not repo:
        print("Failed to load {file}".format(file=args.repo))
        sys.exit(1)
    f.close()

    nr = {}
    nr["name"] = args.name
    nr["description"] = args.desc
    nr["upstream"] = args.upstream
    nr["protected_branches"] = ["master"]
    nr["type"] = "public"

    if repo["community"] == "openeuler":
        repo["repositories"].append(nr)
    elif repo["community"] == "src-openeuler":
        nr["upstream"] = args.upstream
        repo["repositories"].append(nr)

    repo["repositories"].sort(key=lambda r: r["name"])

    valid_sig = False
    for s in sigs["sigs"]:
        if s["name"] == args.sig:
            s["repositories"].append(repo["community"]+"/"+args.name)
            s["repositories"].sort()
            valid_sig=True
            continue

    if valid_sig:
        f = open(args.repo, "w")
        yaml.dump(repo, f)
        f.close()
        f = open(args.sigs, "w")
        yaml.dump(sigs, f)
        f.close()
    else:
        print("SIG name is not valid")
        sys.exit(1)
