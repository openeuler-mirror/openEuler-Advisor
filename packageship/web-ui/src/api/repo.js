/**
 * @file  包管理接口配置文件
 * */

import appAjax from './../libs/ajax-utils';
export const packages = ({
    pageNum,
    pageSize,
    tableName,
    queryPkgName,
    maintainer,
    maintainlevel
}) => {
    return new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/packages',
            type: 'get',
            params: {
                page_num: pageNum,
                page_size: pageSize,
                table_name: tableName,
                query_pkg_name: queryPkgName,
                maintainer,
                maintainlevel
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
export const productVersion = () => {
    return new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/lifeCycle/tables',
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

export const tableCol = () => {
    return new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/packages/tablecol',
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

export const packageDetail = ({table_name, pkg_name}) => {
    return new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/packages/packageInfo',
            type: 'get',
            params: {
                table_name,
                pkg_name
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

export const maintainer = () => {
    return new Promise((resolve, reject) => {
        appAjax.postJson({
            url: '/lifeCycle/maintainer',
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