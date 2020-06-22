"""
    url set
"""
from . import view

urls = [
    # Get all packages' info
    (view.Packages, '/packages', {'query': ('GET')}),


    # Query and update a package info
    (view.SinglePack, '/packages/findByPackName',
     {'query': ('GET'), 'write': ('PUT')}),

    # Query a package's install depend(support querying in one or more databases)
    (view.InstallDepend, '/packages/findInstallDepend', {'query': ('POST')}),

    # Query a package's build depend(support querying in one or more databases)

    (view.BuildDepend, '/packages/findBuildDepend', {'query': ('POST')}),

    # Query a package's all dependencies including install and build depend
    # (support quering a binary or source package in one or more databases)
    (view.SelfDepend, '/packages/findSelfDepend', {'query': ('POST')}),

    # Query a package's all be dependencies including be installed and built depend
    (view.BeDepend, '/packages/findBeDepend', {'query': ('POST')}),

    # Get all imported databases, import new databases and update existed databases

    (view.Repodatas, '/repodatas', {'query': ('GET'), 'write': ('DELETE')}),

    # Reload database
    (view.InitSystem, '/initsystem', {'write': ('POST')})
]
