#!/usr/bin/python3
'''
    Interception before request
'''
from flask import request
from packageship.application import OPERATION
from packageship.application.apps.package.url import urls


__all__ = ['identity_verification']


def identity_verification():
    '''
        Requested authentication
    '''
    if request.url_rule:
        url_rule = request.url_rule.rule
        for view, url, authentication in urls:
            if url == url_rule and OPERATION in authentication.keys():
                if request.method not in authentication.get(OPERATION):
                    return False
                break
        return True

    return False
