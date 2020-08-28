#!/usr/bin/python3
"""
Life cycle of url giant whale collection
"""
from . import view

urls = [  # pylint: disable=invalid-name
    # Download package data or iSsue data
    (view.DownloadFile, '/lifeCycle/download/<file_type>', {'query': ('GET')}),
    # Get a collection of maintainers list
    (view.MaintainerView, '/lifeCycle/maintainer', {'query': ('GET')}),
    # Get the columns that need to be displayed by default in the package
    (view.TableColView, '/packages/tablecol', {'query': ('GET')}),
    # View all table names in the package-info database
    (view.LifeTables, '/lifeCycle/tables', {'query': ('GET')}),
    (view.IssueView, '/lifeCycle/issuetrace', {'query': ('GET')}),
    (view.IssueType, '/lifeCycle/issuetype', {'query': ('GET')}),
    (view.IssueStatus, '/lifeCycle/issuestatus', {'query': ('GET')}),
    (view.IssueCatch, '/lifeCycle/issuecatch', {'write': ('POST')}),
# update a package info
    (view.UpdatePackages, '/lifeCycle/updatePkgInfo', {'write': ('PUT')})
]
