from flask import request
from flask_restful import Resource
from flask import jsonify
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from packageship.libs.log import Log

LOGGER = Log(__name__)

class Packages(Resource):
    '''
    Description: interface for package info management
    Restful API: get
    changeLog:
    '''

    def get(self, *args, **kwargs):
        '''
        Description: Get all package info from a database
        input:
            dbName
        return:
            json file contain package's info
        Exception:
        Changelog：
        '''
        pass


class SinglePack(Resource):
    '''
    description: single package management
    Restful API: get、put
    ChangeLog:
    '''

    def get(self, *args, **kwargs):
        '''
        description: Searching a package info
        input:
            sourceName
            dbName
        return:
            json file contain package's detailed info
        exception:
        changeLog:
        '''
        pass

    def put(self, *args, **kwargs):
        '''
        Description: update a package info
        input:
            packageName
            dbName
            maintainer
            maintainLevel
        return:
        exception:
        changeLog:
        '''
        pass


class InstallDepend(Resource):
    '''
    Description: install depend of binary package
    Restful API: post
    changeLog:
    '''

    def post(self, *args, **kwargs):
        '''
        Description: Query a package's install depend(support
                     querying in one or more databases)
        input:
            binaryName
            dbPreority：the array for database preority
        return:
            resultList[
                result[
                    binaryName: binary package name
                    srcName: the source package name for
                             that binary packge
                    dbName:
                    type: install  install or build, which
                          depend on the function
                    parentNode: the binary package name which is
                                the install depend for binaryName
                ]
            ]
        exception:
        changeLog:
        '''
        pass


class BuildDepend(Resource):
    '''
    Description: build depend of binary package
    Restful API: post
    changeLog:
    '''
    def post(self, *args, **kwargs):
        '''
        Description: Query a package's build depend and
                     build depend package's install depend
                     (support querying in one or more databases)
        input:
            sourceName ：
            dbPreority：the array for database preority
        return:
            resultList[
                restult[
                    binaryName:
                    srcName:
                    dbName:
                    type: install or build, which depend 
                          on the function
                    parentNode: the binary package name which is
                                the build/install depend for binaryName
                ]
            ]
        exception:
        changeLog:
        '''
        pass


class SelfDepend(Resource):
    '''
    Description: querying install and build depend for a package
                 and others which has the same src name
    Restful API: post
    changeLog:
    '''

    def post(self, *args, **kwargs):
        '''
        description: Query a package's all dependencies including install and build depend
                        (support quering a binary or source package in one or more databases)
        input:
            packageName:
            packageType: source/binary
            selfBuild :0/1
            withSubpack: 0/1
            dbPreority：the array for database preority
        return:
            resultList[
                restult[
                    binaryName:
                    srcName:
                    dbName:
                    type: install or build, which depend on the function
                    parentNode: the binary package name which is the
                                build/install depend for binaryName
                ]
            ]

        exception:
        changeLog:
        '''
        pass


class BeDepend(Resource):
    '''
    Description: querying be installed and built depend for a package
                 and others which has the same src name
    Restful API: post
    changeLog:
    '''

    def post(self, *args, **kwargs):
        '''
        description: Query a package's all dependencies including
                     be installed and built depend
        input:
            packageName:
            withSubpack: 0/1
            dbname:
        return:
            resultList[
                restult[
                    binaryName:
                    srcName:
                    dbName:
                    type: beinstall or bebuild, which depend on the function
                    childNode: the binary package name which is the be built/installed depend for binaryName
                ]
            ]
        exception:
        changeLog:
        '''
        pass


class Repodatas(Resource):
    """API for operating databases"""

    def get(self, *args, **kwargs):
        '''
        description: get all database
        input:
        return:
            databasesName
            status
            priority
        exception:
        changeLog:
        '''
        pass

    def delete(self, *args, **kwargs):
        '''
        description: get all database
        input: database name
        return:
        '''

class InitSystem(Resource):
    '''InitSystem'''

    def post(self, *args, **kwargs):
        """
        description: InitSystem
        input:
        return:
        exception:
        changeLog:
        """
        pass

