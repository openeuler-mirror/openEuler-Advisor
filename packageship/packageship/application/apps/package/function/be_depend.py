#!/usr/bin/python3
"""
Description:The dependencies of the query package
    Used for package deletion and upgrade scenarios
    This includes both install and build dependencies
Class: BeDepend
"""
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import literal_column
from flask import current_app
from packageship.libs.dbutils import DBHelper
from packageship.application.models.package import SrcPack
from packageship.application.apps.package.function.constants import ResponseCode


class BeDepend():
    """
    Description: Find the dependencies of the source package
    Attributes:
        source_name: source name
        db_name: database name
        with_sub_pack: with_sub_pack
        source_name_set:Source package lookup set
        bin_name_set:Bin package lookup set
        result_dict:return json
    """

    def __init__(self, source_name, db_name, with_sub_pack):
        """
        init class
        """
        self.source_name = source_name
        self.db_name = db_name
        self.with_sub_pack = with_sub_pack
        self.source_name_set = set()
        self.bin_name_set = set()
        self.result_dict = dict()

    def main(self):
        """
            Description: Map the database, if the source
            package of the query is not in the database,
         throw an exception. Directly to the end
            Args:
            Returns:
                "source name": [
                "source",
                "version",
                "dbname",
                [
                    [
                        "root",
                        null
                    ]
                ]
                ]
            Raises:
        """
        with DBHelper(db_name=self.db_name) as data_base:
            src_obj = data_base.session.query(
                SrcPack).filter_by(name=self.source_name).first()
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
                    [self.source_name], data_base, package_type='src')

        return self.result_dict

    def package_bedepend(self, pkg_name_list, data_base, package_type):
        """
            Description: Query the dependent function
            Args:
                pkg_name_list:source or binary packages name
                data_base: database
                package_type: package type
            Returns:
            Raises:
                SQLAlchemyError: Database connection exception
        """
        search_set = set(pkg_name_list)
        # package_type
        if package_type == 'src':
            name_in = literal_column('src_name').in_(search_set)
        if package_type == 'bin':
            name_in = literal_column('name').in_(search_set)

        sql_str = text("""
            SELECT b1.name AS search_bin_name,
            b1.version AS search_bin_version,
            b1.src_name AS source_name,
            b2.name AS bin_name,
            s1.name AS bebuild_src_name,
            b2.src_name AS install_depend_src_name
            FROM ( SELECT pkgKey,src_name,name,version FROM bin_pack WHERE {} ) b1
            LEFT JOIN bin_provides ON bin_provides.pkgKey = b1.pkgKey
            LEFT JOIN bin_requires br ON br.name = bin_provides.name
            LEFT JOIN src_requires sr ON sr.name = bin_provides.name
            LEFT JOIN src_pack s1 ON s1.pkgKey = sr.pkgKey
            LEFT JOIN bin_pack b2 ON b2.pkgKey = br.pkgKey;""".format(name_in))

        try:
            if package_type == 'src':
                result = data_base.session.execute(
                    sql_str, {
                        'src_name_{}'.format(i): v for i, v in enumerate(
                            search_set, 1)}).fetchall()
            if package_type == 'bin':
                result = data_base.session.execute(
                    sql_str, {
                        'name_{}'.format(i): v for i, v in enumerate(
                            search_set, 1)}).fetchall()

        except SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            return ResponseCode.response_json(ResponseCode.CONNECT_DB_ERROR)

        if result is None:
            return
        # Source and binary packages that were found to be dependent
        source_name_list = []
        bin_name_list = []
        for obj in result:
            if obj.source_name is None:
                source_name = 'NOT FOUND'
            else:
                source_name = obj.source_name
            if obj.bebuild_src_name:
                # Determine if the source package has been checked
                parent_node = obj.bebuild_src_name
                be_type = "build"
                # Call the spell dictionary function
                self.make_dicts(
                    obj.search_bin_name,
                    source_name,
                    obj.search_bin_version,
                    parent_node,
                    be_type)

                if obj.bebuild_src_name not in self.source_name_set:
                    self.source_name_set.add(obj.bebuild_src_name)
                    source_name_list.append(obj.bebuild_src_name)

            if obj.bin_name:
                # Determine if the bin package has been checked
                parent_node = obj.bin_name
                be_type = "install"
                # Call the spell dictionary function
                self.make_dicts(
                    obj.search_bin_name,
                    source_name,
                    obj.search_bin_version,
                    parent_node,
                    be_type)

                if obj.bin_name not in self.bin_name_set:
                    self.bin_name_set.add(obj.bin_name)
                    bin_name_list.append(obj.bin_name)

                    # With_sub_pack=1
                    if self.with_sub_pack == "1":
                        if obj.install_depend_src_name not in self.source_name_set:
                            self.source_name_set.add(
                                obj.install_depend_src_name)
                            source_name_list.append(
                                obj.install_depend_src_name)

        # Sqlite older versions default to a single query with a maximum of 999
        # parameters
        if 0 < len(source_name_list) < 999:
            self.package_bedepend(
                source_name_list, data_base, package_type="src")
        elif len(source_name_list) >= 999:
            count = len(source_name_list) // 999
            for i in range(count + 1):
                self.package_bedepend(
                    source_name_list[999 * i:999 * (i + 1)], data_base, package_type="src")

        if 0 < len(bin_name_list) < 999:
            self.package_bedepend(bin_name_list, data_base, package_type="bin")
        elif len(bin_name_list) >= 999:
            count = len(bin_name_list) // 999
            for i in range(count + 1):
                self.package_bedepend(
                    bin_name_list[999 * i:999 * (i + 1)], data_base, package_type="bin")

    def make_dicts(self, key, source_name, version, parent_node, be_type):
        """
            Description: Splicing dictionary function
            Args:
                 key: dependent bin name
                 source_name: source name
                 version: version
                 parent_node: Rely on package name
                 be_type: dependent type
            Returns:
            Raises:
        """
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
            if [parent_node, be_type] not in self.result_dict[key][-1]:
                self.result_dict[key][-1].append([
                    parent_node,
                    be_type
                ])
