"""
module of issue API
"""
import logging
from flask import request
from flask import Blueprint
from patch_tracking.database.models import Issue
from patch_tracking.api.constant import ResponseCode

log = logging.getLogger(__name__)
issue = Blueprint('issue', __name__)


@issue.route('', methods=["GET"])
def get():
    """
    Returns list of issue.
    """
    if not request.args:
        issues = Issue.query.all()
    else:
        allowed_key = ['repo', 'branch']
        input_params = request.args
        data = dict()
        for k, param in input_params.items():
            if k in allowed_key:
                data[k] = param
            else:
                return ResponseCode.ret_message(ResponseCode.INPUT_PARAMETERS_ERROR)
        issues = Issue.query.filter_by(**data).all()
    resp_data = list()
    for item in issues:
        resp_data.append(item.to_json())
    return ResponseCode.ret_message(code=ResponseCode.SUCCESS, data=resp_data)
