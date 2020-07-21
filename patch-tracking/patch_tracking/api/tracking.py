"""
module of issue API
"""
import logging
from flask import request, Blueprint
from patch_tracking.database.models import Tracking
from patch_tracking.api.business import create_tracking, update_tracking
from patch_tracking.api.constant import ResponseCode
from patch_tracking.util.auth import auth

logger = logging.getLogger(__name__)
tracking = Blueprint('tracking', __name__)


@tracking.route('', methods=["GET"])
def get():
    """
    Returns list of tracking
    """
    if not request.args:
        trackings = Tracking.query.all()
    else:
        required_params = ['repo', 'branch', 'enabled']
        input_params = request.args
        data = dict()
        for k, param in input_params.items():
            if k in required_params:
                if k == 'enabled':
                    param = bool(param == 'true')
                data[k] = param
                required_params.remove(k)
            else:
                return ResponseCode.gen_dict(ResponseCode.INPUT_PARAMETERS_ERROR)

        if 'repo' in required_params and 'branch' not in required_params:
            return ResponseCode.gen_dict(ResponseCode.INPUT_PARAMETERS_ERROR)

        trackings = Tracking.query.filter_by(**data).all()

    resp_data = list()
    for item in trackings:
        resp_data.append(item.to_json())
    return ResponseCode.gen_dict(code=ResponseCode.SUCCESS, data=resp_data)


@tracking.route('', methods=["POST"])
@auth.login_required
def post():
    """
    Creates os update a tracking.
    """
    required_params = ['version_control', 'scm_repo', 'scm_branch', 'scm_commit', 'repo', 'branch', 'enabled']
    input_params = request.json
    data = dict()
    for item in input_params:
        if item in required_params:
            data[item] = input_params[item]
            required_params.remove(item)
        else:
            return ResponseCode.gen_dict(ResponseCode.INPUT_PARAMETERS_ERROR)

    if required_params:
        if len(required_params) == 1 and required_params[0] == 'scm_commit':
            pass
        else:
            return ResponseCode.gen_dict(ResponseCode.INPUT_PARAMETERS_ERROR)
    if data['version_control'] != 'github':
        return ResponseCode.gen_dict(ResponseCode.INPUT_PARAMETERS_ERROR)

    track = Tracking.query.filter_by(repo=data['repo'], branch=data['branch']).first()
    if track:
        try:
            update_tracking(data)
            logger.info('Update tracking. Data: %s.', data)
        except Exception as exception:
            return ResponseCode.gen_dict(code=ResponseCode.INSERT_DATA_ERROR, data=exception)
    else:
        try:
            create_tracking(data)
            logger.info('Create tracking. Data: %s.', data)
        except Exception as exception:
            return ResponseCode.gen_dict(code=ResponseCode.INSERT_DATA_ERROR, data=exception)
    return ResponseCode.gen_dict(code=ResponseCode.SUCCESS, data=request.json)
