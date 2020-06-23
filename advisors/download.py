#!/usr/bin/true
"""
download tar package with url
"""
import os
import sys
import io
import pycurl

def do_curl(url, dest=None):
    """
    Perform a curl operation for url.
    If perform failure or write to dest failure,
    the program exiting with an error.
    """
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.FAILONERROR, True)
    c.setopt(c.CONNECTTIMEOUT, 10)
    c.setopt(c.TIMEOUT, 600)
    c.setopt(c.LOW_SPEED_LIMIT, 1)
    c.setopt(c.LOW_SPEED_TIME, 10)
    buf = io.BytesIO()
    c.setopt(c.WRITEDATA, buf)
    try:
        c.perform()
    except pycurl.error as e:
        print("Unable to fetch {}: {} or tarball path is wrong".format(url, e))
        sys.exit(1)
    finally:
        c.close()

    if dest:
        try:
            with open(dest, 'wb') as fp:
                fp.write(buf.getvalue())
        except IOError as e:
            if os.path.exists(dest):
                os.unlink(dest)
            print("Unable to write to {}: {}".format(dest, e))
            sys.exit(1)

