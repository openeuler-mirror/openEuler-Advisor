#!/usr/bin/python3
"""
Description: marshmallow serialize
"""
from marshmallow import Schema
from marshmallow import fields
from marshmallow import ValidationError
from marshmallow import validate


class PackagesSchema(Schema):
    """
    Description: PackagesSchema serialize
    """
    dbName = fields.Str(validate=validate.Length(
        max=50), required=False, allow_none=True)


class GetpackSchema(Schema):
    """
    Description: GetpackSchema serialize
    """
    sourceName = fields.Str(
        required=True,
        validate=validate.Length(min=1,
                                 max=200))

    dbName = fields.Str(validate=validate.Length(
        max=30), required=False, allow_none=True)
    version = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)


def validate_maintainlevel(maintainlevel):
    """
    Description: Method test
    Args：
        maintainlevel: maintainlevel
    Returns:
        True or failure
    Raises:
        ValidationError: Test failed
    """
    if maintainlevel not in ['1', '2', '3', '4']:
        raise ValidationError("maintainLevel is illegal data ")


class PutpackSchema(Schema):
    """
    Description: PutpackSchema serialize
    """
    sourceName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))
    dbName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=50))
    maintainer = fields.Str(validate=validate.Length(
        max=50), required=False, allow_none=True)
    maintainlevel = fields.Str(
        validate=validate_maintainlevel,
        required=False,
        allow_none=True)


class InstallDependSchema(Schema):
    """
    Description: InstallDependSchema
    """
    binaryName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1, max=500))
    db_list = fields.List(fields.String(), required=False, allow_none=True)


class BuildDependSchema(Schema):
    """
    Description: BuildDependSchema serialize
    """
    sourceName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1, max=200))
    db_list = fields.List(fields.String(), required=False, allow_none=True)


def validate_withsubpack(withsubpack):
    """
    Description: Method test
    Args：
        withsubpack: withsubpack
    Returns:
        True or failure
    Raises:
        ValidationError: Test failed
    """
    if withsubpack not in ['0', '1']:
        raise ValidationError("withSubpack is illegal data ")


class BeDependSchema(Schema):
    """
    Description: BeDependSchema serialize
    """
    packagename = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))
    withsubpack = fields.Str(
        validate=validate_withsubpack,
        required=False, allow_none=True)
    dbname = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=50))


def validate_selfbuild(selfbuild):
    """
    Description: Method test
    """
    if selfbuild not in ['0', '1']:
        raise ValidationError("selfbuild is illegal data ")


def validate_packtype(packtype):
    """
    Description: Method test
    """
    if packtype not in ['source', 'binary']:
        raise ValidationError("packtype is illegal data ")


class SelfDependSchema(Schema):
    """
    Description: SelfDependSchema serialize
    """
    packagename = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))
    db_list = fields.List(fields.String(), required=False, allow_none=True)
    selfbuild = fields.Str(validate=validate_selfbuild,
                           required=False, allow_none=True)
    withsubpack = fields.Str(
        validate=validate_withsubpack, required=False, allow_none=True)
    packtype = fields.Str(validate=validate_packtype,
                          required=False, allow_none=True)


class DeletedbSchema(Schema):
    """
    Description: DeletedbSchema serialize
    """
    dbName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))


def have_err_db_name(db_list, db_priority):
    """
    Description: have error database name method
    Args:
        db_list: db_list db list of inputs
        db_priority: db_priority default list
    Returns:
        If any element in db_list  is no longer in db_priority, return false
    Raises:
    """
    return any(filter(lambda db_name: db_name not in db_priority, db_list))


class InitSystemSchema(Schema):
    """
    Description: InitSystemSchema serialize
    """
    configfile = fields.Str(
        validate=validate.Length(
            max=50), required=False, allow_none=True)
