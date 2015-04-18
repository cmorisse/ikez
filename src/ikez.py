# coding: utf-8
import argparse
import platform
import os
import subprocess
import colorama
from colorama import Fore
import sys
from system import process_system_command
from postgresql import process_postgresql_command
from odoo import process_odoo_command
from system_info import System, process_status_command
import system_info

PROG = "ikez"
DESCRIPTION = "A tool to automate Odoo server development."
EPILOG = "Copyright (c) 2013, 2014, 2015 Cyril MORISSE / @cmorisse\nikez is licenced under GPL3"
VERSION = '0.1.4'
#
# Main entry point
#
def main():
    if len(sys.argv) == 1:
        sys.argv.append('--help')

    parser = argparse.ArgumentParser(prog='ikez', description=DESCRIPTION, epilog=EPILOG)
    subparsers = parser.add_subparsers(dest='command_group')

    # Status sub parser
    status_parser = subparsers.add_parser('status',
                                          help="Display ikez system status")

    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--json',
                        action='store_true',
                        help="Switch ikez output to json.")
    parser.add_argument('--training',
                        action='store_true',
                        help="Display each command before it is executed")
    parser.add_argument('--dryrun',
                        action='store_true',
                        default=False,
                        help="Do not execute commands. Best used with --training.")
    parser.add_argument('--no-packages-update',
                        action='store_true',
                        default=False,
                        help="Don't update system packages index (eg. apt-get update).")
    parser.add_argument('--no-packages-check',
                        action='store_true',
                        default=False,
                        help="Neither check nor install system packages (eg. apt-get install git).")
    parser.add_argument('--no-wkhtmltopdf',
                        action='store_true',
                        default=False,
                        help="Don't install wkhtmltopdf.")
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')

    # postgreSQL sub parser
    pg_parser = subparsers.add_parser('postgresql', help="PostgreSQL setup related commands")
    pg_subparsers = pg_parser.add_subparsers(dest='command')

    pg_install_parser = pg_subparsers.add_parser("install", help="install PostgreSQL server")
    pg_install_parser.add_argument('-l', '--locale',
                                  action='store',
                                  default=None,
                                  help="Locale to setup for PostgresSQL to use it.")

    pg_createuser_parser = pg_subparsers.add_parser("createuser", help="create a dedicated Odoo server postgresql user")
    pg_createuser_parser.add_argument('--username', '-u',
                                      action='store',
                                      default=None,
                                      help="PostgresSQL username create or update (default is $USER).")
    pg_createuser_parser.add_argument('--password', '-p',
                                      action='store',
                                      #dest='db_password',
                                      default=None,  # must be converted to $USER
                                      help="PostgresSQL user password to use or create (default is username)")

    # System sub parser
    sys_parser = subparsers.add_parser('system', help="system setup related commands")
    sys_subparsers = sys_parser.add_subparsers(dest='command')

    sys_inst_packages_parser = sys_subparsers.add_parser("install-dependencies", help="install Odoo required system packages")

    sys_inst_virtualenv_parser = sys_subparsers.add_parser("install-virtualenv", help="install virtualenv '%s' and setuptools '%s'" % ('12.0.7', '14.1.1',))
    sys_inst_virtualenv_parser.add_argument('-f', '--force',
                                            action='store_true',
                                            default=None,
                                            help="force installation of virtualenv {version} and setuptools {version}")

    sys_inst_wkhtml = sys_subparsers.add_parser("install-wkhtmltopdf", help="install wkhtmltopdf")

    # odoo sub-parser
    odoo_parser = subparsers.add_parser('odoo', help="odoo setup related commands")
    odoo_subparsers = odoo_parser.add_subparsers(dest='command')

    odoo_install_parser = odoo_subparsers.add_parser("install",
                                                     help="Install an Odoo server based on muppy appserver templates")
    odoo_install_parser.add_argument('--username', '-u',
                                      action='store',
                                      default=None,
                                      required=True,
                                      help="PostgresSQL username Odoo will use to connect to database server")
    odoo_install_parser.add_argument('--password', '-p',
                                     action='store',
                                     default=None,
                                     help="PostgresSQL password Odoo will use to connect to database server (default=username).")
    odoo_install_parser.add_argument('--admin', '-a',
                                     action='store',
                                     default='admin',
                                     help="Odoo admin password (used to manipulate databases, default='admin') that will be configured.")
    odoo_install_parser.add_argument('--host', '-H',
                                      action='store',
                                      default='127.0.0.1',
                                      help="PostgresSQL server Odoo will connect to (default is '127.0.0.1').")
    odoo_install_parser.add_argument('--locale', '-l',
                                     action='store',
                                     required=False,
                                     default=None,
                                     help="Locale to setup for PostgresSQL to use it.")
    odoo_install_parser.add_argument('--no-buildout-output',
                                     action='store_true',
                                     required=False,
                                     default=False,
                                     help="By default, ikez display 'bin/buildout' output. Use this option to hide the output.")

    odoo_install_parser.add_argument('--force', '-f',
                                      action='store_true',
                                      default=False,
                                      help="Do what will be prompted otherwise (eg. regenerate buildout.cfg, update DB user password,...). Note that --force takes precedence over --unattended")
    odoo_install_parser.add_argument('--force-appserver-cfg',
                                      action='store_true',
                                      default=False,
                                      help="Fore appserver.cfg to be regenerated.")
    odoo_install_parser.add_argument('--unattended',
                                     action='store_true',
                                     default=False,
                                     help="To use for server installation ; if something is missing don't prompt,"
                                          "return an error.")
    odoo_install_parser.add_argument('--index', '-i',
                                     action='store',
                                     default='',
                                     help="URL of an alternate PyPI index server that will be injected un buildout.cfg and used to build server.")
    odoo_install_parser.add_argument('--repository', '-r',
                                     action='store',
                                     default=None,
                                     help="Git URL if the Odoo appserver ikez repository to install")
    odoo_install_parser.add_argument('--destination', '-d',
                                     action='store',
                                     default=None,
                                     required=False,
                                     help="Appserver local destination folder (relative to current directory).")
    odoo_install_parser.add_argument('--no-pip',
                                     action='store_true',
                                     default=False,
                                     help="Do not install pip in the appserver virtualenv")

    odoo_reset_parser = odoo_subparsers.add_parser("reset",
                                                   help="Reset Odoo installation by removing all buildout generated files.")

    odoo_bootstrap_buildout_parser = odoo_subparsers.add_parser("bootstrap-buildout",
                                                                help="Create a virtualenv and bootstrap a buildout")
    odoo_bootstrap_buildout_parser.add_argument('--force', '-f',
                                                action='store_true',
                                                default=False,
                                                help="Do what will be prompted otherwise (eg. regenerate buildout.cfg, update DB user password,...). Note that --force takes precedence over --unattended")
    odoo_bootstrap_buildout_parser.add_argument('--force-appserver-cfg',
                                                action='store_true',
                                                default=False,
                                                help="Fore appserver.cfg to be regenerated.")
    odoo_bootstrap_buildout_parser.add_argument('--index', '-i',
                                                action='store',
                                                default='',
                                                help="URL of an alternate PyPI index server that will be injected un buildout.cfg and used to build server.")
    odoo_bootstrap_buildout_parser.add_argument('--no-pip',
                                                action='store_true',
                                                default=False,
                                                help="Do not install pip in the appserver virtualenv")

    odoo_bootstrap_buildout_parser.add_argument('--username', '-u',
                                                action='store',
                                                default=None,
                                                required=True,
                                                help="PostgresSQL username Odoo will use to connect to database server")
    odoo_bootstrap_buildout_parser.add_argument('--password', '-p',
                                                action='store',
                                                default=None,
                                                help="PostgresSQL password Odoo will use to connect to database server (default=--username).")
    odoo_bootstrap_buildout_parser.add_argument('--admin', '-a',
                                                action='store',
                                                default='admin',
                                                help="Odoo admin password (used to manipulate databases, default='admin') that will be configured.")
    odoo_bootstrap_buildout_parser.add_argument('--host', '-H',
                                                action='store',
                                                default='127.0.0.1',
                                                help="PostgresSQL server Odoo will connect to (default is '127.0.0.1').")




    args = parser.parse_args()

    system_info.get_status(args)

    if args.command_group == 'system':
        sys.exit(process_system_command(args))
    elif args.command_group == 'postgresql':
        sys.exit(process_postgresql_command(args))
    elif args.command_group == 'odoo':
        sys.exit(process_odoo_command(args))
    elif args.command_group == 'status':
        sys.exit(process_status_command(args))


if __name__ == '__main__':
    colorama.init()
    main()

