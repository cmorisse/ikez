import semver

__author__ = 'cmorisse'

import logging
import platform
import datetime
import dateutil.parser
from dateutil.tz import tzlocal

import semver
import utils

_logger = logging.getLogger("SystemScanner")

# TODO: Rework to use a namedtuple or a singleton

class System:
    postgresql_version = None  # Not installed

    system_name = ''
    system_version = ''
    system_major_version = ''

    hostname = ''

    virtualenv_version = ''
    virtualenv_version_ok = False
    brew_version = ''
    brew_installed_packages = []
    git_version = ''
    linux_packages_index_last_update_timestamp = ''
    linux_packages_index_last_update_age = 999999
    wkhtmltopdf_version = ''
    current_locale = ''
    apple_developer_tools = ''


uname = platform.uname()
System.uname = uname  # stored as a reference: Eg ('darwin', 'Quadro.local', '14.1.0', 'Darwin Kernel Version 14.1.0: Thu Feb 26 19:26:47 PST 2015; root:xnu-2782.10.73~1/RELEASE_X86_64', 'x86_64', 'i386')

# On linux, vagrant
if uname[0] == 'Linux':
    tmp = platform.dist()
    System.system_name = tmp[0].lower()
    System.system_version = tmp[1]
    System.system_major_version = System.system_version.split('.')[0]
else:  # Darwin
    System.system_name = uname[0].lower()  # Darwin, Ubuntu, ...
    System.system_version = uname[2] # 14.1.0
    System.system_major_version = System.system_version.split('.')[0]


def get_hostname(args):
    import socket
    System.hostname = socket.gethostname().split('.')[0]


def check_current_locale():
    exit_code, output = utils.execute(['locale'], capture_output=True)
    if not exit_code:
        output = output.split("\n")
        current_locale = filter(lambda s: s.startswith('LC_COLLATE'), output)[0]
        System.current_locale = current_locale.split("\"")[1]

def check_virtualenv_version():
    exit_code, version = utils.execute(['virtualenv', '--version'], capture_output=True)
    version = '' if exit_code else version.split("\n")[0]
    System.virtualenv_version = version
    if System.virtualenv_version:
        System.virtualenv_version_ok = semver.compare(System.virtualenv_version, '1.9.1') > 0

def check_postgresql_server():
    if System.system_name in ('ubuntu', 'debian',):
        command = [
            'sudo',
            'su',
            'postgres',
            '-c',
            'psql -tAc "select version();"'
        ]
        exit_code, output = utils.execute(command,capture_output=True)
        if exit_code:
            System.postgresql_version = None  # Not installed
        else:
            System.postgresql_version = output.split(' ')[1]

    elif System.system_name == 'darwin':
        command = [
            'psql',
            '-tAc',
            'select version();'
        ]
        exit_code, output = utils.execute(command,capture_output=True)
        if exit_code:
            System.postgresql_version = None  # Not installed
        else:
            System.postgresql_version = output.split(' ')[1]  # No need to remove \n
    else:
        raise NotImplementedError()


#
# Linux
#
# Last system packages index refresh timestamp
#
def get_system_index_packages_age(args):
    if System.system_name in ('debian', 'ubuntu',):
        if args.no_packages_update:
            System.linux_packages_index_last_update_timestamp = '--no-packages-update'
            System.linux_packages_index_last_update_age = 59
            return

        exit_code, output = utils.execute(['ls', '--full-time', '-l', '/var/lib/apt/periodic/update-success-stamp'], capture_output=True)
        if exit_code:
            print "ERROR: Unable to check /var/lib/apt/periodic/update-success-stamp timestamp."
        else:
            output = output.split(' ')
            package_index_timestamp_str = output[5]+' '+output[6]+' '+output[7]
            package_index_timestamp = dateutil.parser.parse(package_index_timestamp_str)
            now = datetime.datetime.now(tz=tzlocal())
            age = now - package_index_timestamp
            System.linux_packages_index_last_update_timestamp = package_index_timestamp
            System.linux_packages_index_last_update_age = int(age.total_seconds())

    elif System.system_name == 'darwin':
        # TODO: use brew doctor
        pass

#
# Darwin
#
def check_apple_developer_tools():
    if System.system_name == 'darwin':
        exit_code, output = utils.execute(['xcode-select', '-p'], capture_output=True)
        if not exit_code:
            System.apple_developer_tools = output.replace('\n','')

def check_brew_version():
    if System.system_name == 'darwin' and not System.apple_developer_tools:
        return

    exit_code, output = utils.execute(['brew', '--version'], capture_output=True)
    if not exit_code:
        System.brew_version = output.replace('\n','')

def check_brew_installed_packages():
    if not System.brew_version:
        System.brew_installed_packages = []
        return

    exit_code, output = utils.execute(['brew', 'list'], capture_output=True)
    if exit_code:
        System.brew_installed_packages = []
        return

    System.brew_installed_packages = output.split('\n')


def check_git_version():
    # On darwin we don't check git version until command line tools are installed
    if System.system_name == 'darwin' and not System.apple_developer_tools:
        return

    exit_code, output = utils.execute(['git', '--version'], capture_output=True)
    if not exit_code:
        System.git_version = output.replace('\n','').split(' ')[2]

def check_wkhtmltopdf_version():
    exit_code, output = utils.execute(['wkhtmltopdf', '--version'], capture_output=True)
    if not exit_code:
        System.wkhtmltopdf_version = output.replace('\n','').split(' ')[1]


#
# Missing system packages
#
# TODO: Add a missing packages for Odoo, Django, ...
# returned by a command

def get_status(args):
    get_hostname(args)
    get_system_index_packages_age(args)
    check_current_locale()
    check_virtualenv_version()
    check_postgresql_server()
    check_apple_developer_tools()
    check_git_version()
    check_brew_version()
    check_brew_installed_packages()
    check_wkhtmltopdf_version()

def print_status(args):
    for e in System.__dict__.keys():
        if not e.startswith('__'):
            print("%s=%s" % (e, System.__dict__[e]))


def process_status_command(args):
    get_status(args)
    print_status(args)
    return 0