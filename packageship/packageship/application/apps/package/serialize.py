"""
marshmallow serialize
"""
from marshmallow import Schema
from marshmallow import fields
from marshmallow import ValidationError
from marshmallow import validate


class PackagesSchema(Schema):
    """
    PackagesSchema serialize
    """
    dbName = fields.Str(validate=validate.Length(
        max=50), required=False, allow_none=True)


class GetpackSchema(Schema):
    """
    GetpackSchema serialize
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
    Method test
    """
    if maintainlevel not in ['1', '2', '3', '4']:
        raise ValidationError("maintainLevel is illegal data ")


class PutpackSchema(Schema):
    """
    PutpackSchema serialize
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
    InstallDependSchema
    """
    binaryName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1, max=500))
    db_list = fields.List(fields.String(), required=False, allow_none=True)


class BuildDependSchema(Schema):
    """
    BuildDependSchema serialize
    """
    sourceName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1, max=200))
    db_list = fields.List(fields.String(), required=False, allow_none=True)


def validate_withsubpack(withsubpack):
    """
    Method test
    """
    if withsubpack not in ['0', '1']:
        raise ValidationError("withSubpack is illegal data ")


class BeDependSchema(Schema):
    """
    BeDependSchema serialize
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
    Method test
    """
    if selfbuild not in ['0', '1']:
        raise ValidationError("selfbuild is illegal data ")


def validate_packtype(packtype):
    """
    Method test
    """
    if packtype not in ['source', 'binary']:
        raise ValidationError("packtype is illegal data ")


class SelfDependSchema(Schema):
    """
    SelfDependSchema serialize
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
    DeletedbSchema serialize
    """
    dbName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))


def have_err_db_name(db_list, db_priority):
    '''
    @param:db_list db list of inputs
    @param:db_priority default list
    return:If any element in db_list  is no longer in db_priority, return false
    '''
    return any(filter(lambda db_name: db_name not in db_priority, db_list))


class InitSystemSchema(Schema):
    """
    InitSystemSchema serialize
    """
    configfile = fields.Str(
        validate=validate.Length(
            max=50), required=False, allow_none=True)
