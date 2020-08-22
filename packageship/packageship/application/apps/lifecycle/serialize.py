#!/usr/bin/python3
"""
Description: marshmallow serialize
"""
from marshmallow import Schema
from packageship.application.models.package import packages_issue, packages


class IssueDownloadSchema(Schema):
    """
        Field serialization for issue file download
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = packages_issue
        fields = ('issue_id', 'issue_url', 'issue_content',
                  'issue_title', 'issue_status', 'pkg_name', 'issue_type', 'related_release')


class PackagesDownloadSchema(Schema):
    """
        Field serialization for package file download
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = packages
        fields = ('name', 'url', 'rpm_license', 'version', 'release', 'release_time',
                  'used_time', 'latest_version', 'latest_version_time',
                  'feature', 'cve', 'defect', 'maintainer', 'maintainlevel')
