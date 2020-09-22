#!/usr/bin/python3
"""
Description:The dependencies of the query package
    Used for package deletion and upgrade scenarios
    This includes both install and build dependencies
Class: BeDepend
"""
import copy
from collections import namedtuple, defaultdict
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import literal_column
from packageship.application.models.package import SrcPack
from packageship.libs.dbutils import DBHelper


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
        self.comm_install_builds = defaultdict(set)
        self.provides_name = set()

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
            self._provides_bedepend(
                [self.source_name], data_base, package_type='src')

        for _, value in self.result_dict.items():
            value[-1] = list(value[-1])
        return self.result_dict

    def _get_provides(self, pkg_name_list, data_base, package_type):
        """
            Description: Query the components provided by the required package
            Args:
                pkg_name_list:source or binary packages name
                data_base: database
                package_type: package type
            Returns:
            Raises:
                SQLAlchemyError: Database connection exception
            """
        res = namedtuple(
            'restuple', [
                'search_bin_name', 'search_bin_version', 'source_name'])
        sql_com = """
                SELECT DISTINCT b1.name AS search_bin_name,
                b1.version AS search_bin_version,
                b1.src_name AS source_name,
                bin_provides.name As pro_name
                FROM ( SELECT pkgKey,src_name,name,version FROM bin_pack WHERE {} ) b1
                LEFT JOIN bin_provides ON bin_provides.pkgKey = b1.pkgKey;"""

        # package_type
        if package_type == 'src':
            literal_name = 'src_name'
        elif package_type == 'bin':
            literal_name = 'name'

        # Query database
        # The lower version of SQLite can look up up to 999 parameters
        # simultaneously, so use 900 sharding queries
        try:
            result = []
            for input_name in (pkg_name_list[i:i + 900]
                               for i in range(0, len(pkg_name_list), 900)):
                name_in = literal_column(literal_name).in_(input_name)
                sql_str = text(sql_com.format(name_in))
                result.extend(data_base.session.execute(
                    sql_str,
                    {
                        literal_name + '_{}'.format(i): v
                        for i, v in enumerate(input_name, 1)
                    }
                ).fetchall())
        except SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            return

        if not result:
            return

        # Process the result of the component
        pro_name_dict = dict()

        _components = set()
        for obj in result:
            if not obj.pro_name:
                continue
            # De-weight components
            if obj.pro_name not in self.comm_install_builds:
                pro_name_dict[obj.pro_name] = res(
                    obj.search_bin_name, obj.search_bin_version, obj.source_name)

            if obj.search_bin_name not in self.result_dict:
                self.result_dict[obj.search_bin_name] = [
                    obj.source_name,
                    obj.search_bin_version,
                    self.db_name,
                    self.comm_install_builds[obj.pro_name]
                    if self.comm_install_builds[obj.pro_name] else {(None, None)}
                ]
            tmp_ = copy.deepcopy(self.comm_install_builds[obj.pro_name])

            tmp_.discard((obj.search_bin_name, 'install'))
            tmp_.discard((obj.search_bin_name, 'build'))

            if (None, None) in self.result_dict[obj.search_bin_name][-1] \
                    and self.comm_install_builds[obj.pro_name]:
                self.result_dict[obj.search_bin_name][-1] = tmp_
            else:
                self.result_dict[obj.search_bin_name][-1].update(tmp_)
        return pro_name_dict

    def _provides_bedepend(self, pkg_name_list, data_base, package_type):
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
        # Query component
        pro_names = self._get_provides(pkg_name_list, data_base, package_type)

        if not pro_names:
            return

        sql_2_bin = """
            SELECT DISTINCT
                b2.name AS bin_name,
                b2.src_name AS install_depend_src_name,
                br.name AS pro_name
            FROM
                ( SELECT name, pkgKey FROM bin_requires WHERE {}) br
                LEFT JOIN bin_pack b2 ON b2.pkgKey = br.pkgKey;
        """

        sql_2_src = """
            SELECT DISTINCT
                s1.name AS bebuild_src_name,
                sr.name AS pro_name
            FROM
                ( SELECT name, pkgKey FROM src_requires WHERE {} ) sr
                LEFT JOIN src_pack s1 ON s1.pkgKey = sr.pkgKey;
        """

        provides_name_list = [pro for pro, _ in pro_names.items()]

        result_2_bin = []
        result_2_src = []
        # Query database
        try:
            for input_name in (
                    provides_name_list[i:i + 900] for i in range(0, len(provides_name_list), 900)):
                name_in = literal_column('name').in_(input_name)
                sql_str_2_bin = text(sql_2_bin.format(name_in))
                result_2_bin.extend(data_base.session.execute(
                    sql_str_2_bin,
                    {
                        'name_{}'.format(i): v
                        for i, v in enumerate(input_name, 1)
                    }
                ).fetchall())
                sql_str_2src = text(sql_2_src.format(name_in))
                result_2_src.extend(data_base.session.execute(
                    sql_str_2src,
                    {
                        'name_{}'.format(i): v
                        for i, v in enumerate(input_name, 1)
                    }
                ).fetchall())
        except SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            return

        source_name_list = []
        bin_name_list = []

        # Process the data that the installation depends on
        for bin_info in result_2_bin:
            temp_bin_pkg = bin_info.bin_name
            temp_sub_src_pkg = bin_info.install_depend_src_name

            #withsubpick ==1
            if self.with_sub_pack == '1' and temp_sub_src_pkg not in self.source_name_set:
                self.source_name_set.add(temp_sub_src_pkg)
                source_name_list.append(temp_sub_src_pkg)

            if temp_bin_pkg not in self.bin_name_set:
                self.bin_name_set.add(temp_bin_pkg)
                bin_name_list.append(temp_bin_pkg)

            if bin_info.pro_name not in self.comm_install_builds:
                self.comm_install_builds[bin_info.pro_name] = {
                    (bin_info.bin_name, 'install')
                }

            elif (bin_info.bin_name, 'install') not in \
                    self.comm_install_builds[bin_info.pro_name]:

                self.comm_install_builds[bin_info.pro_name].add(
                    (bin_info.bin_name, 'install')
                )

            self.make_dicts(
                pro_names.get(bin_info.pro_name).search_bin_name,
                pro_names.get(bin_info.pro_name).source_name,
                pro_names.get(bin_info.pro_name).search_bin_version,
                bin_info.bin_name,
                'install'
            )
        # Process data that is compile-dependent
        for src_info in result_2_src:
            if src_info.bebuild_src_name not in self.source_name_set:
                self.source_name_set.add(src_info.bebuild_src_name)
                source_name_list.append(src_info.bebuild_src_name)

            if src_info.pro_name not in self.comm_install_builds:
                self.comm_install_builds[src_info.pro_name] = {
                    (src_info.bebuild_src_name, 'build')
                }
            elif (src_info.bebuild_src_name, 'build') not in \
                    self.comm_install_builds[src_info.pro_name]:

                self.comm_install_builds[src_info.pro_name].add(
                    (src_info.bebuild_src_name, 'build')
                )

            self.make_dicts(
                pro_names.get(src_info.pro_name).search_bin_name,
                pro_names.get(src_info.pro_name).source_name,
                pro_names.get(src_info.pro_name).search_bin_version,
                src_info.bebuild_src_name,
                'build'
            )
        # Recursively query all source packages that need to be looked up
        if source_name_list:
            self._provides_bedepend(
                source_name_list, data_base, package_type="src")
        # Recursively query all binary packages that need to be looked up
        if bin_name_list:
            self._provides_bedepend(
                bin_name_list, data_base, package_type="bin")

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
                {
                    (parent_node,
                     be_type
                     )
                }

            ]
        else:
            if be_type and parent_node:
                if (None, None) in self.result_dict[key][-1]:
                    self.result_dict[key][-1] = {
                        (
                            parent_node,
                            be_type
                        )
                    }

                elif (parent_node, be_type) not in self.result_dict[key][-1]:
                    self.result_dict[key][-1].add(
                        (
                            parent_node,
                            be_type
                        )
                    )
