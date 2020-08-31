"""
module of issue API
"""
import logging
from flask import request, Blueprint
from sqlalchemy.exc import SQLAlchemyError
from patch_tracking.database.models import Tracking
from patch_tracking.api.business import create_tracking, update_tracking, delete_tracking
from patch_tracking.api.constant import ResponseCode
from patch_tracking.api.auth import auth

logger = logging.getLogger(__name__)
tracking = Blueprint('tracking', __name__)


@tracking.route('', methods=["DELETE"])
@auth.login_required
def delete():
    """
    Delete tracking(s).
    """
    input_params = request.args
    keys = list(input_params.keys())

    if not keys or "repo" not in keys:
        return ResponseCode.ret_message(ResponseCode.INPUT_PARAMETERS_ERROR)

    if len(set(keys) - {"repo", "branch"}) != 0:
        return ResponseCode.ret_message(ResponseCode.INPUT_PARAMETERS_ERROR)

    try:
        if "branch" in keys:
            if Tracking.query.filter(Tracking.repo == input_params['repo'],
                                     Tracking.branch == input_params['branch']).first():
                delete_tracking(input_params['repo'], input_params['branch'])
                logger.info('Delete tracking repo: %s, branch: %s', input_params['repo'], input_params['branch'])
                return ResponseCode.ret_message(code=ResponseCode.SUCCESS)
            else:
                logger.info(
                    'Delete tracking repo: %s, branch: %s not found.', input_params['repo'], input_params['branch']
                )
                return ResponseCode.ret_message(code=ResponseCode.DELETE_DB_NOT_FOUND)
        else:
            if Tracking.query.filter(Tracking.repo == input_params['repo']).first():
                delete_tracking(input_params['repo'])
                logger.info('Delete tracking repo: %s', input_params['repo'])
                return ResponseCode.ret_message(code=ResponseCode.SUCCESS)
            else:
                logger.info('Delete tracking repo: %s not found.', input_params['repo'])
                return ResponseCode.ret_message(code=ResponseCode.DELETE_DB_NOT_FOUND)
    except SQLAlchemyError as err:
        return ResponseCode.ret_message(code=ResponseCode.DELETE_DB_ERROR, data=err)


@tracking.route('', methods=["GET"])
def get():
    """
    Returns list of tracking
    """
    if not request.args:
        trackings = Tracking.query.all()
    else:
        allowed_key = ['repo', 'branch', 'enabled']
        input_params = request.args

        data = dict()
        for k, param in input_params.items():
            if k in allowed_key:
                if k == 'enabled':
                    param = bool(param == 'true')
                data[k] = param
            else:
                return ResponseCode.ret_message(ResponseCode.INPUT_PARAMETERS_ERROR)
        trackings = Tracking.query.filter_by(**data).all()

    resp_data = list()
    for item in trackings:
        resp_data.append(item.to_json())
    return ResponseCode.ret_message(code=ResponseCode.SUCCESS, data=resp_data)


@tracking.route('', methods=["POST"])
@auth.login_required
def post():
    """
    Creates or update a tracking.
    """
    required_params = ['version_control', 'scm_repo', 'scm_branch', 'scm_commit', 'repo', 'branch', 'enabled']
    input_params = request.json
    data = dict()
    for item in input_params:
        if item in required_params:
            data[item] = input_params[item]
            required_params.remove(item)
        else:
            return ResponseCode.ret_message(ResponseCode.INPUT_PARAMETERS_ERROR)

    if len(required_params) > 1 or (len(required_params) == 1 and required_params[0] != 'scm_commit'):
        return ResponseCode.ret_message(ResponseCode.INPUT_PARAMETERS_ERROR)

    if data['version_control'] != 'github':
        return ResponseCode.ret_message(ResponseCode.INPUT_PARAMETERS_ERROR)

    track = Tracking.query.filter_by(repo=data['repo'], branch=data['branch']).first()
    if track:
        try:
            update_tracking(data)
            logger.info('Update tracking. Data: %s.', data)
        except SQLAlchemyError as err:
            return ResponseCode.ret_message(code=ResponseCode.INSERT_DATA_ERROR, data=err)
    else:
        try:
            create_tracking(data)
            logger.info('Create tracking. Data: %s.', data)
        except SQLAlchemyError as err:
            return ResponseCode.ret_message(code=ResponseCode.INSERT_DATA_ERROR, data=err)
    return ResponseCode.ret_message(code=ResponseCode.SUCCESS, data=request.json)
