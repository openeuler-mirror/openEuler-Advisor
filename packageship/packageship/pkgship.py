'''
    Entry method for custom commands
'''
import os
import json
try:
    import argparse
    import requests
    from requests.exceptions import ConnectionError as ConnErr
    from requests.exceptions import HTTPError
    import prettytable
    from prettytable import PrettyTable
    from packageship.libs.log import Log
    from packageship.libs.exception import Error
    from packageship.libs.configutils.readconfig import ReadConfig
    LOGGER = Log(__name__)
except ImportError as import_error:
    print('Error importing related dependencies, \
            please check if related dependencies are installed')
else:
    from packageship.application.apps.package.function.constants import ResponseCode
    from packageship.application.apps.package.function.constants import ListNode


DB_NAME = 0


def main():
    '''
    Command line tool entry, register related commands
    Args:

    Returns:

    Raises:
        Error: An error occurred while executing the command
    '''
    try:
        packship_cmd = PkgshipCommand()
        packship_cmd.parser_args()
    except Error as error:
        LOGGER.logger.error(error)
        print('command error')


class BaseCommand():
    '''
     Basic attributes used for command invocation
    Attributes:
        write_host: Can write operation single host address
        read_host: Can read the host address of the operation
        headers: Send HTTP request header information
    '''

    def __init__(self):
        self._read_config = ReadConfig()
        self.write_host = None
        self.read_host = None
        self.__http = 'http://'
        self.headers = {"Content-Type": "application/json",
                        "Accept-Language": "zh-CN,zh;q=0.9"}

        self.load_read_host()
        self.load_write_host()

    def load_write_host(self):
        '''
            Address to load write permission
        '''
        wirte_port = self._read_config.get_system('write_port')

        write_ip = self._read_config.get_system('write_ip_addr')

        _write_host = self.__http + write_ip + ":" + wirte_port

        setattr(self, 'write_host', _write_host)

    def load_read_host(self):
        '''
            Address to load write permission
        '''
        read_port = self._read_config.get_system('query_port')

        read_ip = self._read_config.get_system('query_ip_addr')

        _read_host = self.__http + read_ip + ":" + read_port

        setattr(self, 'read_host', _read_host)


class PkgshipCommand(BaseCommand):
    '''
    PKG package command line
    Attributes:
        statistics: Summarized data table
        table: Output table
        columns: Calculate the width of the terminal dynamically
        params: Command parameters
    '''
    parser = argparse.ArgumentParser(
        description='package related dependency management')
    subparsers = parser.add_subparsers(
        help='package related dependency management')

    def __init__(self):
        super(PkgshipCommand, self).__init__()
        self.statistics = dict()
        self.table = PkgshipCommand.create_table(
            ['package name', 'src name', 'version', 'database'])

        # Calculate the total width of the current terminal
        self.columns = int(os.popen('stty size', 'r').read().split()[1])
        self.params = []

    @staticmethod
    def register_command(command):
        '''
        Registration of related commands
        Args:

        Returns:

        Raises:

        '''
        command.register()

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        for command_params in self.params:
            self.parse.add_argument(  # pylint: disable=E1101
                command_params[0],
                type=eval(command_params[1]),  # pylint: disable=W0123
                help=command_params[2],
                default=command_params[3])

    @classmethod
    def parser_args(cls):
        '''
        Register the command line and parse related commands
        Args:

        Returns:

        Raises:
            Error: An error occurred during command parsing
        '''
        cls.register_command(RemoveCommand())
        cls.register_command(InitDatabaseCommand())
        cls.register_command(UpdateDatabaseCommand())
        cls.register_command(AllPackageCommand())
        cls.register_command(UpdatePackageCommand())
        cls.register_command(BuildDepCommand())
        cls.register_command(InstallDepCommand())
        cls.register_command(SelfBuildCommand())
        cls.register_command(BeDependCommand())
        cls.register_command(SingleCommand())
        try:
            args = cls.parser.parse_args()
            args.func(args)
        except Error:
            print('command error')

    def parse_package(self, response_data):
        '''
        Parse the corresponding data of the package
        Args:
            response_data: http request response content
        Returns:

        Raises:

        '''
        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, list):
                for package_item in package_all:
                    row_data = [package_item.get('sourceName'), package_item.get(
                        'dbname'), package_item.get('version'), package_item.get('license')]
                    self.table.add_row(row_data)
        else:
            print(response_data.get('msg'))

    def parse_depend_package(self, response_data):
        '''
        Parsing package data with dependencies
        Args:
            response_data: http request response content
        Returns:

        Raises:

        '''
        bin_package_count = 0
        src_package_count = 0
        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, dict):

                for bin_package, package_depend in package_all.items():
                    # distinguish whether the current data is the data of the root node
                    if isinstance(package_depend, list) and \
                            package_depend[ListNode.SOURCE_NAME] != 'source':

                        row_data = [bin_package,
                                    package_depend[ListNode.SOURCE_NAME],
                                    package_depend[ListNode.VERSION],
                                    package_depend[ListNode.DBNAME]]
                        # Whether the database exists
                        if package_depend[ListNode.DBNAME] not in self.statistics:
                            self.statistics[package_depend[ListNode.DBNAME]] = {
                                'binary': [],
                                'source': []
                            }
                        # Determine whether the current binary package exists
                        if bin_package not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                            self.statistics[package_depend[ListNode.DBNAME]
                                            ]['binary'].append(bin_package)
                            bin_package_count += 1
                        # Determine whether the source package exists
                        if package_depend[ListNode.SOURCE_NAME] not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['source']:
                            self.statistics[package_depend[ListNode.DBNAME]]['source'].append(
                                package_depend[ListNode.SOURCE_NAME])
                            src_package_count += 1

                        if hasattr(self, 'table') and self.table:
                            self.table.add_row(row_data)
        else:
            LOGGER.logger.error(response_data.get('msg'))
            print(response_data.get('msg'))
        statistics_table = self.statistics_table(
            bin_package_count, src_package_count)
        return statistics_table

    def print_(self, content=None, character='=', dividing_line=False):
        '''
        Output formatted characters
        Args:
           content: Output content
           character: Output separator content
           dividing_line: Whether to show the separator
        Returns:

        Raises:

        '''
        # Get the current width of the console

        if dividing_line:
            print(character * self.columns)
        if content:
            print(content)
        if dividing_line:
            print(character * self.columns)

    @staticmethod
    def create_table(title):
        '''
        Create printed forms
        Args:

        Returns:

        Raises:

        '''
        table = PrettyTable(title)
        # table.set_style(prettytable.PLAIN_COLUMNS)
        table.align = 'l'
        table.horizontal_char = '='
        table.junction_char = '='
        table.vrules = prettytable.NONE
        table.hrules = prettytable.FRAME
        return table

    def statistics_table(self, bin_package_count, src_package_count):
        '''
        Generate data for total statistical tables
        Args:
            bin_package_count: Number of binary packages
            src_package_count: Number of source packages
        Returns:
            Summarized data table
        Raises:

        '''
        statistics_table = self.create_table(['', 'binary', 'source'])
        statistics_table.add_row(
            ['self depend sum', bin_package_count, src_package_count])

        # cyclically count the number of source packages and binary packages in each database
        for database, statistics_item in self.statistics.items():
            statistics_table.add_row([database, len(statistics_item.get(
                'binary')), len(statistics_item.get('source'))])
        return statistics_table

    @staticmethod
    def http_error(response):
        '''
        Log error messages for http
        Args:
            response: Response content of http request
        Returns:

        Raises:
            HTTPError: http request error
        '''
        try:
            print(response.raise_for_status())
        except HTTPError as http_error:
            LOGGER.logger.error(http_error)
            print('Request failed')
            print(http_error)


class RemoveCommand(PkgshipCommand):
    '''
    Delete database command
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    '''

    def __init__(self):
        super(RemoveCommand, self).__init__()
        self.parse = PkgshipCommand.subparsers.add_parser(
            'rm', help='delete database operation')
        self.params = [('db', 'str', 'name of the database operated', '')]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(RemoveCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        '''
        Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnErr: Request connection error

        '''
        if params.db is None:
            print('No database specified for deletion')
        else:
            _url = self.write_host + '/repodatas?dbName={}'.format(params.db)
            try:
                response = requests.delete(_url)
            except ConnErr as conn_err:
                LOGGER.logger.error(conn_err)
                print(str(conn_err))
            else:
                # Determine whether to delete the mysql database or sqlite database
                if response.status_code == 200:
                    data = json.loads(response.text)
                    if data.get('code') == ResponseCode.SUCCESS:
                        print('delete success')
                    else:
                        LOGGER.logger.error(data.get('msg'))
                        print(data.get('msg'))
                else:
                    self.http_error(response)


class InitDatabaseCommand(PkgshipCommand):
    '''
    Initialize  database command
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    '''

    def __init__(self):
        super(InitDatabaseCommand, self).__init__()
        self.parse = PkgshipCommand.subparsers.add_parser(
            'init', help='initialization of the database')
        self.params = [
            ('-filepath', 'str', 'name of the database operated', '')]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(InitDatabaseCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        '''
        Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:

        '''
        file_path = params.filepath
        try:
            response = requests.post(self.write_host +
                                     '/initsystem', data=json.dumps({'configfile': file_path}),
                                     headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                response_data = json.loads(response.text)
                if response_data.get('code') == ResponseCode.SUCCESS:
                    print('Database initialization success ')
                else:
                    LOGGER.logger.error(response_data.get('msg'))
                    print(response_data.get('msg'))
            else:
                self.http_error(response)


class UpdateDatabaseCommand(PkgshipCommand):
    '''
    update  database command
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    '''

    def __init__(self):
        super(UpdateDatabaseCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'updatedb', help='database update operation')
        self.params = [('db', 'str', 'name of the database operated', '')]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(UpdateDatabaseCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        '''
        Action to execute command
        Args:

        Returns:

        Raises:

        '''
        pass  # pylint: disable= W0107


class AllPackageCommand(PkgshipCommand):
    '''
    get all package commands
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        table: Output table
    '''

    def __init__(self):
        super(AllPackageCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'list', help='get all package data')
        self.table = self.create_table(
            ['packagenames', 'database', 'version', 'license'])
        self.params = [('-db', 'str', 'name of the database operated', '')]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(AllPackageCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        '''
        Action to execute command
        Args:

        Returns:

        Raises:
            ConnectionError: Request connection error
        '''
        _url = self.read_host + \
            '/packages?dbName={dbName}'.format(dbName=params.db)
        try:
            response = requests.get(_url)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:

                self.parse_package(json.loads(response.text))
                if self.table:
                    print(self.table)
            else:
                self.http_error(response)


class UpdatePackageCommand(PkgshipCommand):
    '''
    update package data
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    '''

    def __init__(self):
        super(UpdatePackageCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'updatepkg', help='update package data')
        self.params = [
            ('packagename', 'str', 'Source package name', ''),
            ('db', 'str', 'name of the database operated', ''),
            ('-m', 'str', 'Maintainers name', ''),
            ('-l', 'int', 'database priority', 1)
        ]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(UpdatePackageCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        '''
        Action to execute command
        Args:

        Returns:

        Raises:
            ConnectionError: Request connection error
        '''
        _url = self.write_host + '/packages/findByPackName'
        try:
            response = requests.put(
                _url, data=json.dumps({'sourceName': params.packagename,
                                       'dbName': params.db,
                                       'maintainer': params.m,
                                       'maintainlevel': params.l}),
                headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                data = json.loads(response.text)
                if data.get('code') == ResponseCode.SUCCESS:
                    print('update completed')
                else:
                    LOGGER.logger.error(data.get('msg'))
                    print(data.get('msg'))
            else:
                self.http_error(response)


class BuildDepCommand(PkgshipCommand):
    '''
    query the compilation dependencies of the specified package
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        collection: Is there a collection parameter
        collection_params: Command line collection parameters
    '''

    def __init__(self):
        super(BuildDepCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'builddep', help='query the compilation dependencies of the specified package')
        self.collection = True
        self.params = [
            ('packagename', 'str', 'source package name', ''),
        ]
        self.collection_params = [
            ('-dbs', 'Operational database collection')
        ]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(BuildDepCommand, self).register()
        # collection parameters

        for cmd_params in self.collection_params:
            self.parse.add_argument(
                cmd_params[0], nargs='*', default=None, help=cmd_params[1])
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        '''
        Action to execute command
        Args:

        Returns:

        Raises:
            ConnectionError: Request connection error
        '''
        _url = self.read_host + '/packages/findBuildDepend'
        try:
            response = requests.post(
                _url, data=json.dumps({'sourceName': params.packagename,
                                       'db_list': params.dbs}),
                headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                statistics_table = self.parse_depend_package(
                    json.loads(response.text))
                if getattr(self.table, 'rowcount'):
                    self.print_('query {} buildDepend  result display:'.format(
                        params.packagename))
                    print(self.table)
                    self.print_('statistics')
                    print(statistics_table)
            else:
                self.http_error(response)


class InstallDepCommand(PkgshipCommand):
    '''
    query the installation dependencies of the specified package
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        collection: Is there a collection parameter
        collection_params: Command line collection parameters
    '''

    def __init__(self):
        super(InstallDepCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'installdep', help='query the installation dependencies of the specified package')
        self.collection = True
        self.params = [
            ('packagename', 'str', 'source package name', ''),
        ]
        self.collection_params = [
            ('-dbs', 'Operational database collection')
        ]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(InstallDepCommand, self).register()
        # collection parameters

        for cmd_params in self.collection_params:
            self.parse.add_argument(
                cmd_params[0], nargs='*', default=None, help=cmd_params[1])
        self.parse.set_defaults(func=self.do_command)

    def parse_package(self, response_data):
        '''
        Parse the corresponding data of the package
        Args:
            response_data: http response data
        Returns:

        Raises:

        '''
        if getattr(self, 'statistics'):
            setattr(self, 'statistics', dict())
        bin_package_count = 0
        src_package_count = 0
        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, dict):
                for bin_package, package_depend in package_all.items():
                    # distinguish whether the current data is the data of the root node
                    if isinstance(package_depend, list) and package_depend[-1][0][0] != 'root':

                        row_data = [bin_package,
                                    package_depend[ListNode.SOURCE_NAME],
                                    package_depend[ListNode.VERSION],
                                    package_depend[ListNode.DBNAME]]
                        # Whether the database exists
                        if package_depend[ListNode.DBNAME] not in self.statistics:
                            self.statistics[package_depend[ListNode.DBNAME]] = {
                                'binary': [],
                                'source': []
                            }
                        # Determine whether the current binary package exists
                        if bin_package not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                            self.statistics[package_depend[ListNode.DBNAME]
                                            ]['binary'].append(bin_package)
                            bin_package_count += 1
                        # Determine whether the source package exists
                        if package_depend[ListNode.SOURCE_NAME] not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['source']:
                            self.statistics[package_depend[ListNode.DBNAME]]['source'].append(
                                package_depend[ListNode.SOURCE_NAME])
                            src_package_count += 1

                        self.table.add_row(row_data)
        else:
            LOGGER.logger.error(response_data.get('msg'))
            print(response_data.get('msg'))
        # Display of aggregated data
        statistics_table = self.statistics_table(
            bin_package_count, src_package_count)

        return statistics_table

    def do_command(self, params):
        '''
        Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnectionError: requests connection error
        '''
        _url = self.read_host + '/packages/findInstallDepend'
        try:
            response = requests.post(_url, data=json.dumps(
                {
                    'binaryName': params.packagename,
                    'db_list': params.dbs
                }, ensure_ascii=True), headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                statistics_table = self.parse_package(
                    json.loads(response.text))
                if getattr(self.table, 'rowcount'):
                    self.print_('query{} InstallDepend result display:'.format(
                        params.packagename))
                    print(self.table)
                    self.print_('statistics')
                    print(statistics_table)
            else:
                self.http_error(response)


class SelfBuildCommand(PkgshipCommand):
    '''
    self-compiled dependency query
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        collection: Is there a collection parameter
        collection_params: Command line collection parameters
    '''

    def __init__(self):
        super(SelfBuildCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'selfbuild', help='query the self-compiled dependencies of the specified package')
        self.collection = True
        self.bin_package_table = self.create_table(
            ['package name', 'src name', 'version', 'database'])
        self.src_package_table = self.create_table([
            'src name', 'version', 'database'])
        self.params = [
            ('packagename', 'str', 'source package name', ''),
            ('-t', 'str', 'Source of data query', 'binary'),
            ('-w', 'str', 'whether to include other subpackages of binary', 0),
            ('-s', 'str', 'whether it is self-compiled', 0)
        ]

        self.collection_params = [
            ('-dbs', 'Operational database collection')
        ]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(SelfBuildCommand, self).register()
        # collection parameters

        for cmd_params in self.collection_params:
            self.parse.add_argument(
                cmd_params[0], nargs='*', default=None, help=cmd_params[1])
        self.parse.set_defaults(func=self.do_command)

    def _parse_bin_package(self, bin_packages):
        '''
            Parsing binary result data
        '''
        bin_package_count = 0
        if bin_packages:
            for bin_package, package_depend in bin_packages.items():
                # distinguish whether the current data is the data of the root node
                if isinstance(package_depend, list) and package_depend[-1][0][0] != 'root':

                    row_data = [bin_package, package_depend[ListNode.SOURCE_NAME],
                                package_depend[ListNode.VERSION], package_depend[ListNode.DBNAME]]

                    # Whether the database exists
                    if package_depend[ListNode.DBNAME] not in self.statistics:
                        self.statistics[package_depend[ListNode.DBNAME]] = {
                            'binary': [],
                            'source': []
                        }
                    # Determine whether the current binary package exists
                    if bin_package not in \
                            self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                        self.statistics[package_depend[ListNode.DBNAME]
                                        ]['binary'].append(bin_package)
                        bin_package_count += 1
                    self.bin_package_table.add_row(row_data)

        return bin_package_count

    def _parse_src_package(self, src_apckages):
        '''
            Source package data analysis
        '''
        src_package_count = 0
        if src_apckages:
            for src_package, package_depend in src_apckages.items():
                # distinguish whether the current data is the data of the root node
                if isinstance(package_depend, list):

                    row_data = [src_package, package_depend[ListNode.VERSION],
                                package_depend[DB_NAME]]
                    # Whether the database exists
                    if package_depend[DB_NAME] not in self.statistics:
                        self.statistics[package_depend[DB_NAME]] = {
                            'binary': [],
                            'source': []
                        }
                    # Determine whether the current binary package exists
                    if src_package not in self.statistics[package_depend[DB_NAME]]['source']:
                        self.statistics[package_depend[DB_NAME]
                                        ]['source'].append(src_package)
                        src_package_count += 1

                    self.src_package_table.add_row(row_data)

        return src_package_count

    def parse_package(self, response_data):
        '''
        Parse the corresponding data of the package
        Args:
            response_data: http response data
        Returns:
            Summarized data table
        Raises:

        '''
        if getattr(self, 'statistics'):
            setattr(self, 'statistics', dict())
        bin_package_count = 0
        src_package_count = 0

        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, dict):
                # Parsing binary result data
                bin_package_count = self._parse_bin_package(
                    package_all.get('binary_dicts'))

                # Source package data analysis
                src_package_count = self._parse_src_package(
                    package_all.get('source_dicts'))
        else:
            LOGGER.logger.error(response_data.get('msg'))
            print(response_data.get('msg'))
        # Display of aggregated data
        statistics_table = self.statistics_table(
            bin_package_count, src_package_count)
        # return (bin_package_table, src_package_table, statistics_table)
        return statistics_table

    def do_command(self, params):
        '''
        Action to execute command
        Args:
            params: commands lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        '''
        _url = self.read_host + '/packages/findSelfDepend'
        try:
            response = requests.post(_url,
                                     data=json.dumps({
                                         'packagename': params.packagename,
                                         'db_list': params.dbs,
                                         'packtype': params.t,
                                         'selfbuild': str(params.s),
                                         'withsubpack': str(params.w)}),
                                     headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                statistics_table = self.parse_package(
                    json.loads(response.text))
                if getattr(self.bin_package_table, 'rowcount') \
                        and getattr(self.src_package_table, 'rowcount'):
                    self.print_('query {} selfDepend result display :'.format(
                        params.packagename))
                    print(self.bin_package_table)
                    self.print_(character='=')
                    print(self.src_package_table)
                    self.print_('statistics')
                    print(statistics_table)
            else:
                self.http_error(response)


class BeDependCommand(PkgshipCommand):
    '''
    dependent query
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    '''

    def __init__(self):
        super(BeDependCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'bedepend', help='dependency query for the specified package')
        self.params = [
            ('packagename', 'str', 'source package name', ''),
            ('db', 'str', 'name of the database operated', ''),
            ('-w', 'str', 'whether to include other subpackages of binary', 0),
        ]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(BeDependCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        '''
        Action to execute command
        Args:
            params: command lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        '''
        _url = self.read_host + '/packages/findBeDepend'
        try:
            response = requests.post(_url, data=json.dumps(
                {
                    'packagename': params.packagename,
                    'dbname': params.db,
                    'withsubpack': str(params.w)
                }
            ), headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                statistics_table = self.parse_depend_package(
                    json.loads(response.text))
                if getattr(self.table, 'rowcount'):
                    self.print_('query {} beDepend result display :'.format(
                        params.packagename))
                    print(self.table)
                    self.print_('statistics')
                    print(statistics_table)
            else:
                self.http_error(response)


class SingleCommand(PkgshipCommand):
    '''
    query single package information
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    '''

    def __init__(self):
        super(SingleCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'single', help='query the information of a single package')
        self.params = [
            ('packagename', 'str', 'source package name', ''),
            ('-db', 'str', 'name of the database operated', '')
        ]

    def register(self):
        '''
        Command line parameter injection
        Args:

        Returns:

        Raises:

        '''
        super(SingleCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def parse_package(self, response_data):
        '''
        Parse the corresponding data of the package
        Args:
            response_data: http response data
        Returns:

        Raises:

        '''
        show_field_name = ('sourceName', 'dbname', 'version',
                           'license', 'maintainer', 'maintainlevel')
        print_contents = []
        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, list):
                for package_item in package_all:
                    for key, value in package_item.items():
                        if value is None:
                            value = ''
                        if key in show_field_name:

                            line_content = '%-15s:%s' % (key, value)
                            print_contents.append(line_content)
                    print_contents.append('='*self.columns)
        else:
            print(response_data.get('msg'))
        if print_contents:
            for content in print_contents:
                self.print_(content=content)

    def do_command(self, params):
        '''
        Action to execute command
        Args:
            params: command lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        '''
        _url = self.read_host + \
            '/packages/findByPackName?dbName={db_name}&sourceName={packagename}' \
            .format(db_name=params.db, packagename=params.packagename)
        try:
            response = requests.get(_url)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                self.parse_package(json.loads(response.text))
            else:
                self.http_error(response)


if __name__ == '__main__':
    main()
