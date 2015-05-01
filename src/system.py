__author__ = 'cmorisse'

from system_info import System, print_status, get_system_index_packages_age
import subprocess
import os
import sys
import semver
from colorama import Back, Fore
from utils import pretty_execute, execute, echo, prompt, echo_color_reset, echo_color_set


def assert_sudo_to(msg):
    if os.getuid():
        print "ERROR: You must be root to %s." % msg
        sys.exit(1)

def is_sudo():
    return os.getuid() == 0


def install_packages_debian(package_list, args=None, indent=0):

    if args.no_packages_check:
        echo("System packages and dependencies update skipped.", indent=indent, color=Fore.CYAN)
        return 0

    # update apt-get index
    exit_code = refresh_system_packages_index_debian(args, indent=indent)
    if exit_code:
        return exit_code

    # install each package that is not
    failed = 0

    for package in package_list:
        exit_code, output = execute(['sudo', 'dpkg', '-s', package], capture_output=True)
        if exit_code:  # Not installed
            exit_code = pretty_execute("Installing package: '%s'" % package,
                                       ['sudo', 'apt-get', 'install', '-y', package],
                                       args, indent=indent)
            if exit_code:
                failed = exit_code

    return failed


def set_locale_darwin(locale, args, indent=0):
    if locale == System.current_locale:
        print "Locale '%s' is already the active one." % System.current_locale
        return 0

    # TODO: check asked locale is valid
    language = locale.split('.')[0]
    raise NotImplementedError("set locale not implemented on Darwin")


def set_locale_ubuntu(locale, args, indent=0):
    if locale == System.current_locale:
        echo("Locale '%s' is already the active one." % System.current_locale, indent=indent)
        return 0

    # TODO: check asked locale is valid
    language = locale.split('.')[0]

    # Generate locale
    exit_code = pretty_execute("Generating locale '%s'" % locale,
                               ['sudo', 'locale-gen', locale],
                               args, indent=indent)
    if exit_code:
        return exit_code

    # Update locale
    command = [
        'sudo',
        'update-locale',
        'LANG="%s"' % locale,
        'LANGUAGE="%s"' % language,
        'LC_ALL="%s"' % locale,
        'LC_CTYPE="%s"'% locale
    ]
    exit_code = pretty_execute("Updating locale to '%s'" % locale, command,  args, indent=indent)
    if exit_code:
        return exit_code

    # Reconfigure locales
    command = ['sudo', 'dpkg-reconfigure', 'locales']
    exit_code = pretty_execute("Reconfiguring locales", command,  args, indent=indent)
    return exit_code

#
# System plugin
#
PACKAGES_ubuntu = [
    'python-dev',
    'zlib1g-dev',
    'libpq-dev',
    'libxml2-dev', 'libxslt1-dev',
    'libyaml-dev',
    'libldap2-dev', 'libsasl2-dev',
    'libopenjpeg-dev', 'libjpeg-dev',
    'libfreetype6-dev', 'liblcms2-dev', 'liblcms1-dev', 'libwebp-dev', 'libtiff4-dev',
    'bzr', 'mercurial', 'git', 'vim', 'curl', 'htop', 'gettext',
    ]

PACKAGES_ubuntu_15 = [
    'python-dev',
    'zlib1g-dev',
    'libpq-dev',
    'libxml2-dev', 'libxslt1-dev',
    'libyaml-dev',
    'libldap2-dev', 'libsasl2-dev',
    'libopenjpeg-dev', 'libjpeg-dev',
    'libfreetype6-dev', 'liblcms2-dev', 'libwebp-dev', 'libtiff5-dev',
    'bzr', 'mercurial', 'git', 'vim', 'curl', 'htop', 'gettext',
    ]


PACKAGES_debian_7 = [
    'python-dev',
    'zlib1g-dev',
    'libpq-dev',
    'libxml2-dev', 'libxslt1-dev',
    'libyaml-dev',
    'libldap2-dev', 'libsasl2-dev',
    'libopenjpeg-dev', 'libjpeg8-dev',
    'libfreetype6-dev', 'liblcms2-dev', 'liblcms1-dev', 'libwebp-dev', 'libtiff4-dev',
    'bzr', 'mercurial', 'git', 'vim', 'curl', 'htop', 'gettext',
    ]

PACKAGES_debian_8 = [
    'python-dev',
    'zlib1g-dev',
    'libpq-dev',
    'libxml2-dev', 'libxslt1-dev',
    'libyaml-dev',
    'libldap2-dev', 'libsasl2-dev',
    'libopenjpeg-dev', 'libjpeg62-turbo-dev',
    'libfreetype6-dev', 'liblcms2-dev', 'libwebp-dev', 'libtiff5-dev',
    'bzr', 'mercurial', 'git', 'vim', 'curl', 'htop', 'gettext',
    ]


LINUX_PACKAGES_INDEX_MAX_AGE = 12 * 60 * 60

def refresh_system_packages_index_debian(args, indent=0):

    exit_code = 0
    if System.linux_packages_index_last_update_age > LINUX_PACKAGES_INDEX_MAX_AGE:
        exit_code = pretty_execute("Updating system packages index",
                                   ['sudo', 'apt-get', 'update'], args, indent=indent)
        if not exit_code:
            get_system_index_packages_age(args)

    return exit_code

MAP_UBUNTU_VERSION_TO_PACKAGE_NAME = {
    '12.04': 'wkhtmltox-0.12.1_linux-precise-amd64.deb',
    '14.04': 'wkhtmltox-0.12.1_linux-trusty-amd64.deb',
    '15.04': 'wkhtmltox-0.12.1_linux-trusty-amd64.deb',
}
MAP_DEBIAN_VERSION_TO_PACKAGE_NAME = {
    '7':   'wkhtmltox-0.12.1_linux-wheezy-amd64.deb',
    '8':   'wkhtmltox-0.12.2.1_linux-jessie-amd64.deb',
}


def install_wkhtmltopdf_debian(args, indent=0):

    print "%sInstalling wkhtmltopdf 0.12.1 (required by Odoo v8 and above to print QWeb reports)" % ('    ' * indent,)
    if System.system_name == 'debian':
        if System.system_major_version == '7':
            package_list = ['fontconfig', 'libfontconfig1', 'libpng12-0']
        else:
            package_list = ['fontconfig', 'libfontconfig1', 'libpng12-0', 'xfonts-base', 'xfonts-75dpi']


    else:  # Ubuntu
        package_list = ['fontconfig', 'libfontconfig1', 'libjpeg-turbo8']


    exit_code = install_packages_debian(package_list, args, indent=indent+1)
    if exit_code:
        return exit_code

    if System.system_name == 'debian':
        package_file_name = MAP_DEBIAN_VERSION_TO_PACKAGE_NAME[System.system_major_version]
        if System.system_major_version == '7':
            package_url =  'http://downloads.sourceforge.net/project/wkhtmltopdf/archive/0.12.1/'

        else:
            package_url = 'http://downloads.sourceforge.net/project/wkhtmltopdf/0.12.2.1/'
        command = [
            'wget',
            package_url + package_file_name
        ]
    else:
        package_file_name = MAP_UBUNTU_VERSION_TO_PACKAGE_NAME[System.system_version]
        command = [
            'wget',
            'http://downloads.sourceforge.net/project/wkhtmltopdf/archive/0.12.1/' + package_file_name
        ]


    if not os.path.exists(package_file_name):
        exit_code = pretty_execute("Downloading wkhtmltopdf 0.12.1", command, args, indent=indent+1)
        if exit_code:
            return exit_code

    command = [
        'sudo',
        'dpkg', '-i', package_file_name
    ]
    exit_code = pretty_execute("Installing wkhtmltopdf 0.12.1", command, args, indent=indent+1)
    return exit_code


WKHTMLTOPDF_REQUIRED_VERSION = '0.12.1'  # TODO= move to global settings


def install_wkhtmltopdf(args, indent=0):
    if args.no_wkhtmltopdf:
        echo("wkhtmltopdf installation skipped.", indent=indent, color=Fore.CYAN)
        return 0

    if not System.wkhtmltopdf_version:
        if System.system_name in ('debian', 'ubuntu',):
            return install_wkhtmltopdf_debian(args, indent=indent)
        else:
            raise NotImplemented()

    # wkhtmltopdf is installed.
    # We warn user if installed version is different than ikez expected one
    if System.wkhtmltopdf_version != WKHTMLTOPDF_REQUIRED_VERSION:
        echo("WARNING: wkhtmltopdf is already installed at version '%s' "
             "while odoo v8 require '%s'." % (System.wkhtmltopdf_version,
                                              WKHTMLTOPDF_REQUIRED_VERSION,),
             indent=indent)
    return 0


def install_system_dependencies_ubuntu(args, indent=0):

    # apt-get install
    if System.system_name == 'debian':
        if System.system_major_version == '7':
            exit_code = install_packages_debian(PACKAGES_debian_7, args, indent=indent)
        else:
            exit_code = install_packages_debian(PACKAGES_debian_8, args, indent=indent)

    else:  # Ubuntu
        if System.system_major_version == '15':
            exit_code = install_packages_debian(PACKAGES_ubuntu_15, args, indent=indent)
        else:
            exit_code = install_packages_debian(PACKAGES_ubuntu, args, indent=indent)

    if exit_code:
        return exit_code

    # wkhtmltopdf
    exit_code = install_wkhtmltopdf(args, indent=indent)
    if exit_code:
        return exit_code
    return 0


#
# Darwin
#
def install_packages_darwin(package_list, args=None, indent=0):
    # TODO: On Darwin, we don't bother to refresh since brew index is upto date at install
    # exit_code = refresh_system_packages_index_darwin(args, indent=indent)
    #if exit_code:
    #    return exit_code

    # install each package that is not
    failed = 0

    for package in package_list:
        if package not in System.brew_installed_packages:
            exit_code = pretty_execute("Installing package: '%s'" % package,
                                       ['brew', 'install', package],
                                       args, indent=indent)
            if exit_code:
                failed = exit_code

    return failed


def install_xcode(args, indent=0):
    echo("On Darwin, developer tools must be installed from Apple servers.", indent=indent, color=Fore.CYAN)
    echo("On the window that will open, click on \"Get Xcode\", if you want to", indent=indent, color=Fore.CYAN)
    echo("install the full Apple Development Environment (> 1Gb) or click ", indent=indent, color=Fore.CYAN)
    echo("on \"Install\" to only install command line tools required", indent=indent, color=Fore.CYAN)
    echo("by ikez.", indent=indent, color=Fore.CYAN)
    prompt("Press Return when ready and relaunch ikez when it will be done ! ", indent=indent, color=Fore.RED)
    exit_code = pretty_execute("Launching Apple developer tools installer",
                               ['xcode-select', '--install'], args, indent=indent)
    sys.exit(1)


def install_brew(args, indent=0):
    echo("ikez use \"Homebrew\" (aka brew) package manager to install some", indent=indent, color=Fore.CYAN)
    echo("required frameworks (eg. libjpeg)", indent=indent, color=Fore.CYAN)
    echo("and programs (eg. git).", indent=indent, color=Fore.CYAN)
    echo("Homebrew home is http://brew.sh", indent=indent, color=Fore.CYAN)
    echo("You must install brew following instructions on the home page that will open.", indent=indent, color=Fore.CYAN)
    prompt("Press Return when ready and relaunch ikez when it will be done ! ", indent=indent, color=Fore.RED)
    exit_code = pretty_execute("Opening brew homepage",
                               ['open', 'http://brew.sh'],
                               args, indent=indent)
    sys.exit(1)


def install_wkhtmltopdf_darwin(args, indent=0):

    echo("Installing wkhtmltopdf 0.12.1 (required by Odoo v8 and above to print QWeb reports)",
         indent=indent)

    echo("On Darwin, wkhtmltopdf is installed using an interactive installer from wkhtmltopdf", indent=indent+1, color=Fore.CYAN)
    echo("official web site: http://wkhtmltopdf.org", indent=indent+1, color=Fore.CYAN)

    command = [
        'wget',
        'http://downloads.sourceforge.net/project/wkhtmltopdf/archive/0.12.1/'
        'wkhtmltox-0.12.1_osx-cocoa-x86-64.pkg'
    ]
    if not os.path.exists('wkhtmltox-0.12.1_osx-cocoa-x86-64.pkg'):
        exit_code = pretty_execute("Downloading wkhtmltopdf 0.12.1", command, args, indent=indent+1)
        if exit_code:
            return exit_code

    prompt("When you're ready, press Enter to launch wkhtmltopdf installer then relaunch"
           " ikez when it will be done ! ", indent=indent+1, color=Fore.RED)
    exit_code = pretty_execute("Launching 'wkhtmltox-0.12.1_osx-cocoa-x86-64.pkg' installer",
                               ['open', 'wkhtmltox-0.12.1_osx-cocoa-x86-64.pkg'], args, indent=indent+1)
    sys.exit(1)


#
# System plugin
#
PACKAGES_darwin = [
    'freetype', 'jpeg', 'libpng', 'little-cms2', 'openjpeg', 'libtiff',
    # 'openjpeg21', TODO: Why does it failed
    'openssl',
    'wget', 'cmake',
    'libxml2', 'libyaml',
    'git', 'mercurial', 'bazaar']


def install_system_dependencies_darwin(args, indent=0):

    # Are xcode or command tools installed ?
    if not System.apple_developer_tools:
        return install_xcode(args, indent=indent)

    if not System.brew_version:
        return install_brew(args, indent=indent)

    # brew install
    exit_code = install_packages_darwin(PACKAGES_darwin, args, indent=indent)
    if exit_code:
        return exit_code

    if not System.wkhtmltopdf_version:
        return install_wkhtmltopdf_darwin(args, indent=indent)

    return exit_code


def install_system_dependencies(args, indent=0):

    if args.no_packages_check:
        echo("System packages and dependencies update skipped.", indent=indent, color=Fore.CYAN)
        return 0

    echo("Checking required system packages and dependencies", indent=indent)

    if System.system_name in ('ubuntu', 'debian',):
        return install_system_dependencies_ubuntu(args, indent=indent+1)

    elif System.system_name == 'darwin':
        return install_system_dependencies_darwin(args, indent=indent+1)
    else:
        raise NotImplemented()

#
# virtualenv
#
def install_virtualenv_from_pypi(args, indent=0):
    exit_code = pretty_execute("Downloading setuptools",
                               ['wget', '--no-check-certificate', 'https://bootstrap.pypa.io/ez_setup.py'],
                               args, indent=indent)
    if exit_code:
        return exit_code
    exit_code = pretty_execute("Installing setuptools",
                               ['sudo', 'python', 'ez_setup.py', '--version=14.1.1'],
                               args, indent=indent)
    if exit_code:
        return exit_code
    exit_code = pretty_execute("Installing virtualenv",
                               ['sudo', 'easy_install', 'virtualenv==12.0.7'],
                               args, indent=indent)
    if exit_code:
        return exit_code

    # TODO: fix this ; files are not deleted
    exit_code = pretty_execute("Cleaning",
                               ['rm', '-f', 'easy_setup.py', 'setuptools-14.1.1.zip'],
                               args, indent=indent)
    return exit_code


def install_virtualenv(args, indent=0):

    echo("Installing virtualenv", indent)

    if not System.virtualenv_version:
        echo("virtualenv is not installed !!!!", indent+1, Fore.CYAN)
        echo("ikez (and buildout) requires a virtualenv version > 1.9.1", indent+1, Fore.CYAN)

        if System.system_name == 'debian':
            if System.system_major_version == '7':
                echo("On Wheezy (Debian 7.8), default virtualenv version is too old for ikez (and buildout).", indent=indent+1,
                     color=Fore.CYAN)
                echo("So we will install recent setuptools (14.1.1) and virtualenv (12.0.7) from pypi.", indent=indent+1, color=Fore.CYAN)
                echo("Please look there for detail:", indent=indent+1, color=Fore.CYAN)
                echo("  - https://pypi.python.org/pypi/setuptools", indent=indent+1, color=Fore.CYAN)
                echo("  - https://pypi.python.org/pypi/virtualenv", indent=indent+1, color=Fore.CYAN)
                if not args.force:
                    user_permission = (prompt("Are you Ok ? [Y/n] ", indent=indent+1, color=Fore.RED) or 'Y').lower() in ['y', 'yes', 'o',                                                                                                                          'oui']
                    if not user_permission:
                        return 1

                return install_virtualenv_from_pypi(args, indent=indent+1)

            elif System.system_major_version == '8':
                echo("On Jessie (Debian 8), default virtualenv version is too old for ikez (and buildout).", indent=indent+1,
                     color=Fore.CYAN)
                echo("So we will install recent setuptools (14.1.1) and virtualenv (12.0.7) from pypi.", indent=indent+1, color=Fore.CYAN)
                echo("Please look there for detail:", indent=indent+1, color=Fore.CYAN)
                echo("  - https://pypi.python.org/pypi/setuptools", indent=indent+1, color=Fore.CYAN)
                echo("  - https://pypi.python.org/pypi/virtualenv", indent=indent+1, color=Fore.CYAN)
                if not args.force:
                    user_permission = (prompt("Are you Ok ? [Y/n] ", indent=indent+1, color=Fore.RED) or 'Y').lower() in ['y', 'yes', 'o',                                                                                                                          'oui']
                    if not user_permission:
                        return 1

                return install_virtualenv_from_pypi(args, indent=indent+1)

            else:
                echo("You are running ikez on an unsupported Debian version ! ikez supports only"
                     "precise and trusty for now.", color=Fore.RED)
                raise NotImplementedError()

        elif System.system_name == 'ubuntu':

            if System.system_major_version == '12':
                echo("On Precise (Ubuntu 12), default virtualenv version is too old for ikez (and buildout).", indent=indent+1,
                     color=Fore.CYAN)
                echo("So we will install recent setuptools (14.1.1) and virtualenv (12.0.7) from pypi.", indent=indent+1, color=Fore.CYAN)
                echo("Please look there for detail:", indent=indent+1, color=Fore.CYAN)
                echo("  - https://pypi.python.org/pypi/setuptools", indent=indent+1, color=Fore.CYAN)
                echo("  - https://pypi.python.org/pypi/virtualenv", indent=indent+1, color=Fore.CYAN)
                if not args.force:
                    user_permission = (prompt("Are you Ok ? [Y/n] ", indent=indent+1, color=Fore.RED) or 'Y').lower() in ['y', 'yes', 'o',                                                                                                                          'oui']
                    if not user_permission:
                        return 1

                return install_virtualenv_from_pypi(args, indent=indent+1)

            elif System.system_major_version in ('14', '15',):
                echo("On Ubuntu 14 and 15, default virtualenv version is ok so we just apt-get it.",
                     indent=indent+1, color=Fore.CYAN)
                exit_code = pretty_execute("Installing Ubuntu distribution virtualenv",
                                           ['sudo', 'apt-get', 'install', '-y', 'python-virtualenv'],
                                           args, indent=indent+1)
                return exit_code
            else:
                echo("You are running ikez on an unsupported Ubuntu version ! ikez supports only "
                     "Ubuntu 14 and 15 for now.", color=Fore.RED)
                raise NotImplementedError()

        elif System.system_name == 'darwin':
            echo("On Darwin / MacOS, we install recent setuptools (14.1.1) and virtualenv (12.0.7) from pypi.", indent=indent+1, color=Fore.CYAN)
            echo("Please look there for detail:", indent=indent+1, color=Fore.CYAN)
            echo("  - https://pypi.python.org/pypi/setuptools", indent=indent+1, color=Fore.CYAN)
            echo("  - https://pypi.python.org/pypi/virtualenv", indent=indent+1, color=Fore.CYAN)
            if not args.force:
                user_permission = (prompt("Are you Ok ? [Y/n] ", indent=indent+1, color=Fore.RED) or 'Y').lower() in ['y', 'yes', 'o',                                                                                                                          'oui']
                if not user_permission:
                    return 1

            return install_virtualenv_from_pypi(args, indent=indent+1)

        else:
            raise NotImplementedError()

    elif semver.compare(System.virtualenv_version, '1.9.1') > 0:
        print "No need to install virtualenv ;  installed version ('%s') is ok (> '1.9.1')." % System.virtualenv_version
        return 126
    else:
        echo("Installed virtualenv version '%s' is too old ! " % System.virtualenv_version, indent=indent+1, color=Fore.CYAN)
        echo("ikez requires virtualenv version > 1.9.1", indent=indent+1, color=Fore.CYAN)
        echo("Look at: ", indent=indent+1, color=Fore.CYAN)
        echo("  - https://pypi.python.org/pypi/setuptools", indent=indent+1, color=Fore.CYAN)
        echo("  - https://pypi.python.org/pypi/virtualenv", indent=indent+1, color=Fore.CYAN)

    return 1  #


def process_system_command(args):
    if args.command == 'install-dependencies':
        exit_code = install_system_dependencies(args)
    elif args.command == 'install-virtualenv':
        exit_code = install_virtualenv(args)
    elif args.command == 'install-wkhtmltopdf':
        exit_code = install_wkhtmltopdf(args)
    else:
        raise NotImplementedError(args.command)
    sys.exit(exit_code)
