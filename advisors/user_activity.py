#!/usr/bin/python3
"""
This is a command line tool to collect activities for maintainers of given SIG
"""

import os
import json
import urllib
import urllib.request
import urllib.parse
import argparse
import datetime
import yaml

class Advisor:
    """
    This is a object abstract TC robot
    """
    def __init__(self):
        self.secret = open(os.path.expanduser("~/.gitee_personal_token.json"), "r")
        self.token = json.load(self.secret)
        self.header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) "\
                       "Gecko/20100101 Firefox/50.0"}
        self.tc_members = None
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"
        self.repositories = []

    def get_json(self, url):
        """
        Return object parsed from remote json
        """
        headers = self.header.copy()
        headers["Content-Type"] = "application/json;charset=UTF-8"
        req = urllib.request.Request(url=url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as result:
            resp = json.loads(result.read().decode("utf-8"))
        return resp

    def get_file(self, repo, path):
        """
        Get remote raw file
        """
        url = "https://gitee.com/{repo}/raw/master/{path}".format(repo=repo, path=path)
        req = urllib.request.Request(url=url, headers=self.header, method="GET")
        with urllib.request.urlopen(req) as result:
            resp = result.read()
        return resp

    def get_pub_events(self, username, limit, ignore_memberevent, ignore_nonsigevent):
        """
        Get list of public events for given user
        """
        event_list = []
        base = "https://gitee.com/api/v5/users/"
        template = base + "{username}/events/public?access_token={token}&limits=20"
        events_url = template.format(token=self.token['access_token'], username=username)
        #print(events_url)
        events = self.get_json(events_url)

        while len(event_list) < limit and events:
            last_id = ""
            for event in events:
                last_id = event['id']
                if not event['type']:
                    continue
                if ignore_memberevent and event['type'] == 'MemberEvent':
                    continue
                repo_name = event['repo'].get('full_name', "")
                if repo_name == "":
                    print("ERROR: " + str(event['id']))
                if ignore_nonsigevent and self.repositories and repo_name not in self.repositories:
                    continue
                new_event = {}
                new_event['repo'] = repo_name
                new_event['type'] = event['type']
                new_event['date'] = event['created_at']
                event_list.append(new_event.copy())

            new_url = events_url + "&prev_id=" + str(last_id)
            #print(new_url)
            #print(len(event_list))
            events = self.get_json(new_url)

        return event_list

    def get_sig_members(self, sig):
        """
        Get list of current SIG maintainers
        """
        try:
            owners = yaml.load(self.get_file("openeuler/community", "sig/{sig}/sig-info.yaml".format(sig=sig)),
                               Loader=yaml.Loader)
        except urllib.error.HTTPError as err:
            owners = yaml.load(self.get_file("openeuler/community", "sig/{sig}/OWNERS".format(sig=sig)),
                               Loader=yaml.Loader)

        self.tc_members = owners["maintainers"]

        try:
            repositories = owners["repositories"]
        except KeyError as err:
            repositories = []
        if not repositories:
            print("Failed to get repo list for {sig}".format(sig=sig))
        else:
            for repository in repositories:
                repo = yaml.load(str(repository),Loader=yaml.FullLoader)
                for r in repo["repo"]:
                    self.repositories.append(r)

        return owners["maintainers"]

def print_statistic(event_list):
    """
    Print out the statistic of users activity
    """
    event_set = {}
    for event in event_list:
        same_kind = event_set.get(event['type'], set())
        same_kind.add(event['repo'])
        event_set[event['type']] = same_kind

    for k in event_set:
        print("{action}: {l}".format(action=k, l=event_set[k]))

    print("")

def main():
    """
    Main entrance of the functionality
    """
    par = argparse.ArgumentParser()
    par.add_argument("-s", "--sig", help="Name of SIG to be evaluated", default="TC")
    par.add_argument("-n", "--number", help="Number of public events to be processed",
                     default=50, type=int)
    par.add_argument("-m", "--member", help="Count in member change events",
                     default=True, action="store_false")
    par.add_argument("-t", "--strict", help="Not count in events have no relationship with sig repos",
                     default=False, action="store_true")

    args = par.parse_args()

    advisor = Advisor()

    maintainers = advisor.get_sig_members(args.sig)
    if not maintainers:
        print("Failed to get maintainer list for {sig}".format(sig=args.sig))
    print("Current {sig} maintainers: ".format(sig=args.sig))

    for member in maintainers:
        try:
            member_info = json.loads(str(member).replace("\'", "\"").replace("None","\"None\""))
            member_id = member_info['gitee_id']
        except json.decoder.JSONDecodeError as err:
            member_id = member
        eve_list = advisor.get_pub_events(member_id, args.number, args.member, args.strict)
        print("{name}, Total: {number}".format(name=member_id, number=len(eve_list)))
        if eve_list:
            #print("From: {date2}, To: {date1}".format(
            #    date1=eve_list[0]['date'], date2=eve_list[-1]['date']))
            now_day = datetime.datetime.now(datetime.timezone.utc)
            first = datetime.datetime.strptime(eve_list[-1]['date'], advisor.time_format)
            last = datetime.datetime.strptime(eve_list[0]['date'], advisor.time_format)
            duration = last - first
            print("It has been {days} days since last contribution".format(days=(now_day-last).days))
            if duration.days == 0:
                print("Average {:05.2f} activities per day while active".format(len(eve_list)))
            else:
                print("Average {:05.2f} activities per day while active".format(len(eve_list)/duration.days))
            print_statistic(eve_list)

if __name__ == "__main__":
    main()
