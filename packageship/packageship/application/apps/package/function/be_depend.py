# -*- coding:utf-8 -*-
'''
    The dependencies of the query package
    Used for package deletion and upgrade scenarios
    This includes both install and build dependencies
'''
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import literal_column
from flask import current_app
from packageship.libs.dbutils import DBHelper
from packageship.application.models.package import src_pack
from packageship.application.apps.package.function.constants import ResponseCode

class BeDepend:
    '''
    Find the dependencies of the source package
    '''

    def __init__(self, source_name, db_name, with_sub_pack):
        '''
        :param source_name: source_name
        :param db_name: db_name
        :param with_sub_pack: with_sub_pack
        '''
        self.source_name = source_name
        self.db_name = db_name
        self.with_sub_pack = with_sub_pack
        # Source package lookup set
        self.source_name_set = set()
        # Bin package lookup set
        self.bin_name_set = set()
        # return json
        self.result_dict = dict()

    def main(self):
        '''
        Map the database, if the source package of the query is not in the database,
         throw an exception. Directly to the end
        :return:
        '''
        with DBHelper(db_name=self.db_name) as data_base:
            src_obj = data_base.session.query(
                src_pack).filter_by(name=self.source_name).first()
            if src_obj:
                # spell dictionary
                self.result_dict[self.source_name + "_src"] = [
                    "source",
                    src_obj.version,
                    self.db_name,
                    [["root", None]]
                ]
                self.source_name_set.add(self.source_name)
                self.package_bedepend(
                    [src_obj.id], data_base, package_type='src')

        return self.result_dict

    def package_bedepend(self, pkg_id_list, data_base, package_type):
        '''
        Query the dependent function
        :param pkg_id_list:source or binary packages id
        :param data_base: database
        :param package_type: package type
        :return:
        '''
        search_set = set(pkg_id_list)
        id_in = literal_column('id').in_(search_set)
        # package_type
        if package_type == 'src':
            sql_str = text("""
                        SELECT b1.name AS search_bin_name,
                        b1.version AS search_bin_version,
                        src.NAME AS source_name,
                        b2.name AS bin_name,
                        b2.id AS bin_id,
                        s1.name AS bebuild_src_name,
                        s1.id AS bebuild_src_id,
                        s2.name AS install_depend_src_name,
                        s2.id AS  install_depend_src_id
                        FROM
                        ( SELECT id,NAME FROM src_pack WHERE {} ) src
                        LEFT JOIN bin_pack b1 ON b1.srcIDkey = src.id
                        LEFT JOIN pack_provides ON pack_provides.binIDkey = b1.id
                        LEFT JOIN pack_requires ON pack_requires.depProIDkey = pack_provides.id
                        LEFT JOIN src_pack s1 ON s1.id = pack_requires.srcIDkey
                        LEFT JOIN bin_pack b2 ON b2.id = pack_requires.binIDkey
                        LEFT JOIN src_pack s2 ON s2.id = b2.srcIDkey;""".format(id_in))
        if package_type == 'bin':
            sql_str = text("""
                        SELECT b1.name AS search_bin_name,
                        b1.version AS search_bin_version,
                        s3.NAME AS source_name,
                        b2.name AS bin_name,
                        b2.id AS bin_id,
                        s1.name AS bebuild_src_name,
                        s1.id AS bebuild_src_id,
                        s2.name AS install_depend_src_name,
                        s2.id AS  install_depend_src_id
                        FROM
                        (SELECT id,NAME,version,srcIDkey FROM bin_pack WHERE {} ) b1
                        LEFT JOIN src_pack s3 ON s3.id = b1.srcIDkey
                        LEFT JOIN pack_provides ON pack_provides.binIDkey = b1.id
                        LEFT JOIN pack_requires ON pack_requires.depProIDkey = pack_provides.id
                        LEFT JOIN src_pack s1 ON s1.id = pack_requires.srcIDkey
                        LEFT JOIN bin_pack b2 ON b2.id = pack_requires.binIDkey
                        LEFT JOIN src_pack s2 ON s2.id = b2.srcIDkey;
                                """.format(id_in))
        try:
            result = data_base.session.execute(
                sql_str, {
                    'id_{}'.format(i): v for i, v in enumerate(
                        search_set, 1)}).fetchall()
        except SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            return ResponseCode.response_json(ResponseCode.CONNECT_DB_ERROR)

        if result is None:
            return
        # Source and binary packages that were found to be dependent
        source_id_list = []
        bin_id_list = []
        for obj in result:
            if obj.source_name is None:
                source_name = 'NOT FOUND'
            else:
                source_name = obj.source_name
            if obj.bebuild_src_name:
                # Determine if the source package has been checked
                if obj.bebuild_src_name not in self.source_name_set:
                    self.source_name_set.add(obj.bebuild_src_name)
                    source_id_list.append(obj.bebuild_src_id)

                    parent_node = obj.bebuild_src_name
                    be_type = "build"
                    # Call the spell dictionary function
                    self.make_dicts(
                        obj.search_bin_name,
                        source_name,
                        obj.search_bin_version,
                        parent_node,
                        be_type)

            if obj.bin_name:
                # Determine if the bin package has been checked
                if obj.bin_name not in self.bin_name_set:
                    self.bin_name_set.add(obj.bin_name)
                    bin_id_list.append(obj.bin_id)

                    parent_node = obj.bin_name
                    be_type = "install"
                    # Call the spell dictionary function
                    self.make_dicts(
                        obj.search_bin_name,
                        source_name,
                        obj.search_bin_version,
                        parent_node,
                        be_type)
                    # withsubpack=1
                    if self.with_sub_pack == "1":
                        if obj.install_depend_src_name not in self.source_name_set:
                            self.source_name_set.add(
                                obj.install_depend_src_name)
                            source_id_list.append(obj.install_depend_src_id)

        if len(source_id_list) != 0:
            self.package_bedepend(
                source_id_list, data_base, package_type="src")
        if len(bin_id_list) != 0:
            self.package_bedepend(bin_id_list, data_base, package_type="bin")

    def make_dicts(self, key, source_name, version, parent_node, be_type):
        '''
        :param key: dependent bin name
        :param source_name: source name
        :param version: version
        :param parent_node: Rely on package name
        :param be_type: dependent type
        :return:
        '''
        if key not in self.result_dict:
            self.result_dict[key] = [
                source_name,
                version,
                self.db_name,
                [
                    [parent_node,
                     be_type
                     ]
                ]
            ]
        else:
            self.result_dict[key][-1].append([
                parent_node,
                be_type
            ])
