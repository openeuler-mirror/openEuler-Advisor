#!/usr/bin/python3
"""
Blueprint collection trying to page
"""
from packageship.application.apps import package
from packageship.application.apps import lifecycle
from packageship.application.apps import dependinfo

blue_point = [  # pylint: disable=invalid-name
    (package.package, package.api),
    (lifecycle.lifecycle, lifecycle.api),
    (dependinfo.dependinfo, dependinfo.api)
]

__all__ = ['blue_point']
