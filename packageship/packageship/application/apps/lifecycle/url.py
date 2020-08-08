#!/usr/bin/python3
"""
Life cycle of url giant whale collection
"""
from . import view


urls = [
    (view.DownloadFile, '/lifeCycle/download/<file_type>', {'query': ('GET')}),
    (view.MaintainerView, '/lifeCycle/maintainer', {'query': ('GET')}),
    (view.TableColView, '/packages/tablecol', {'query': ('GET')}),

]
