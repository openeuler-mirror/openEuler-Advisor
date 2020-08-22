#!/usr/bin/python3
"""
Description: Interception before request
"""
from flask import request
from packageship import application
from packageship.application.apps.package.url import urls


__all__ = ['identity_verification']


def identity_verification():
    """
    Description: Requested authentication
    Args:
    Returns:
    Raises:
    """
    if request.url_rule:
        url_rule = request.url_rule.rule
        for _view, url, authentication in urls:
            if url.lower() == url_rule.lower() and application.OPERATION in authentication.keys():
                if request.method not in authentication.get(application.OPERATION):
                    return False
                break
        return True

    return False
