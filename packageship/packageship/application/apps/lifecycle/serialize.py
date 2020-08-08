#!/usr/bin/python3
"""
Description: marshmallow serialize
"""
from marshmallow import Schema
from marshmallow import fields
from marshmallow import validate
from packageship.application.models.package import packages_issue, packages


class IssueSchema(Schema):
    """
    Description: IssueSchema serialize
    """
    # openeuler 20
    tableName = fields.Str(
        required=True, validate=validate.Length(min=1, max=200))
    # repo
    packageName = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)
    page = fields.Integer(required=True)
    per_page = fields.Integer(required=True)


class IssueDownloadSchema(Schema):
    """
        Field serialization for issue file download
    """
    class Meta:  # pylint: disable=missing-class-docstring
        model = packages_issue
        fields = ('issue_id', 'issue_url', 'issue_content',
                  'issue_title', 'issue_status', 'name', 'issue_type', 'related_release')


class PackagesDownloadSchema(Schema):
    """
        Field serialization for package file download
    """
    class Meta:  # pylint: disable=missing-class-docstring
        model = packages
        fields = ('name', 'url', 'rpm_license', 'version', 'release', 'release_time',
                  'end_time', 'maintainer_status', 'latest_version', 'latest_version_time',
                  'demand', 'cve', 'defect', 'maintainer', 'maintainlevel', 'feature')
