/**
 * @file  包管理 issue接口配置文件
 * */

import appAjax from './../libs/ajax-utils';
export const issueList = ({
  pageNum,
  pageSize,
  issueType,
  issueStatus
}) => {
    return new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/lifeCycle/issuetrace',
            type: 'get',
            params: {
                page_num: pageNum,
                page_size: pageSize,
                issue_type: issueType,
                issue_status: issueStatus
            },
            success(result) {
                if (result) {
                    resolve(result);
                    return;
                }
                reject(result);
            },
            error(msg) {
                reject(msg);
            }

        });

    });
};

export const issueType = () => {
    return new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/lifeCycle/issuetype',
            type: 'get',
            success(result) {
                if (result) {
                    resolve(result);
                    return;
                }
                reject(result);
            },
            error(msg) {
                reject(msg);
            }

        });

    });
};

export const issueStatus = () =>  new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/lifeCycle/issuestatus',
            type: 'get',
            success(result) {
                if (result) {
                    resolve(result);
                    return;
                }
                reject(result);
            },
            error(msg) {
                reject(msg);
            }

        });

    });
