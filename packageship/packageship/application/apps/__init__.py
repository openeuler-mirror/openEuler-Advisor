#!/usr/bin/python3
"""
Blueprint collection trying to page
"""
from packageship.application.apps.package import package, api as package_api
from packageship.application.apps.lifecycle import lifecycle, api as life_cycle_api

blue_point = [
    (package, package_api),
    (lifecycle, life_cycle_api)
]

__all__ = ['blue_point']
