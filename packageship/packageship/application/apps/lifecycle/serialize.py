#!/usr/bin/python3
"""
Description: marshmallow serialize
"""
from marshmallow import Schema
from marshmallow import fields
from marshmallow import validate
from packageship.application.models.package import PackagesIssue, Packages


class IssueSchema(Schema):
    """
    Description: IssueSchema serialize
    """
    page_num = fields.Integer(required=True)
    page_size = fields.Integer(required=True)
    pkg_name = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)
    maintainer = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)
    issue_type = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)
    issue_status = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)


class IssueDownloadSchema(Schema):
    """
        Field serialization for issue file download
    """

    class Meta:
        """Model mapping serialized fields"""
        model = PackagesIssue
        fields = ('issue_id', 'issue_url', 'issue_content',
                  'issue_title', 'issue_status', 'pkg_name', 'issue_type', 'related_release')


class PackagesDownloadSchema(Schema):
    """
        Field serialization for package file download
    """

    class Meta:
        """Model mapping serialized fields"""
        model = Packages
        fields = ('name', 'url', 'rpm_license', 'version', 'release', 'release_time',
                  'used_time', 'latest_version', 'latest_version_time',
                  'feature', 'cve', 'defect', 'maintainer', 'maintainlevel')


class IssuePageSchema(Schema):
    """
    Description: IssuePageSchema serialize
    """
    maintainer = fields.Str()

    class Meta:  # pylint: disable=missing-class-docstring
        """Model mapping serialized fields"""
        model = PackagesIssue
        fields = ('issue_id', 'issue_url',
                  'issue_title', 'issue_status', 'pkg_name', 'issue_type', 'maintainer')


class UpdateMoreSchema(Schema):
    """
    Description: InitSystemSchema serialize
    """
    tablename = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))
    dbpath = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))
