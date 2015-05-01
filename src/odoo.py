# coding: utf-8
import subprocess
import sys
from colorama import Fore
from postgresql import exec_psql_user_command, pg_test_user_connection
import postgresql
import system
from utils import pretty_execute, echo, prompt


__author__ = 'cmorisse'
import os
from system_info import System

def is_cwd_an_ikez_repo(args):
    """
    Returns True is current directory contains:
     - a project_addons folder
     - buildout.cfg.template file

    :param args:
    :type args:
    :return:
    :rtype:
    """
    test_result = os.path.exists('project_addons') and os.path.exists('buildout.cfg.template')
    if args.verbose:
        print "It seem's we are in a muppy appserver repository. I found:"
        print " - a project_addons/ folder"
        print " - a buildout.cfg.template file"
    return test_result


def enforcing_odoo_server_database_user(args, indent=0):
    """
    Check supplied PostgreSQL user and password are valid
    """

    echo("Enforcing appserver database user", indent=indent)

    if not args.password:
        args.password = args.username

    # test if user exists
    if postgresql.pg_user_exists(args.username, args=args, indent=indent+1):
        # it exists ; is login password ok
        exit_code = pg_test_user_connection(args.username, args.password, args.host, args=args, indent=indent+1)
        if exit_code:
            # No !
            if args.force:
                exit_code = postgresql.pg_set_password(args.username, args.password, args, indent=indent+1)

            elif not args.unattended:
                user_permission = (prompt("User '%s' exists but with another password. Do you want to change his password with '%s' [Y/n] ? " % (args.username, args.password,),
                                          indent=indent+1, color=Fore.RED) or 'Y').lower() in ['y', 'yes', 'o', 'oui']
                if user_permission:
                    exit_code = postgresql.pg_set_password(args.username, args.password, args, indent=indent+2)
            else:
                echo("ERROR: Wrong PostgreSQL password for user '%s'. Aborting Odoo installation." % args.username, indent=indent+1, color=Fore.RED)
                echo("Relaunch install --force or with valid PostgreSQL username and password or create one using 'ikez postgresql createuser' command.", indent=indent+1, color=Fore.RED)
                return exit_code

    else:  # User do not exists, create it
        exit_code = postgresql.pg_create_user(args.username, args.password, args=args, indent=indent+1)

    return exit_code


BUILDOUT_CFG_TEMPLATE = """[buildout]
extends = appserver.cfg
{index}

[openerp]
options.admin_passwd = {admin}
options.db_user = {username}
options.db_password = {password}
options.db_host = {host}
"""


def generate_buildout_cfg(args, indent=0):

    if not os.path.exists('buildout.cfg') or args.force:
        echo("Generating buildout.cfg: ", indent=indent, end='')
        if args.index:
            # TODO: check index is a valid URL pointing to a PYPI server
            args.index = "index = %s" % args.index
        buildout_cfg_content = BUILDOUT_CFG_TEMPLATE.format(**args.__dict__)
        buildout_cfg = open('buildout.cfg', mode='w')
        buildout_cfg.write(buildout_cfg_content)
        buildout_cfg.close()
        echo("Done", indent=0, color=Fore.GREEN)
    else:
        echo("Existing buildout.cfg untouched. Use --force to regenerate it.", indent, Fore.CYAN)

    return 0


APPSERVER_CFG_TEMPLATE = """[buildout]
extends = buildout.cfg.template

#
# Below configure what is different from template.
# Typically you should have here
# [openerp]
# version = url http://nightly.odoo.com/8.0/nightly/src/odoo_8.0.latest.tar.gz
# addons = 	local ./project_addons/
#			git git@bitbucket.org:cmorisse/inouk_openerp_data_migration_toolkit.git parts/inouk_openerp_data_migration_toolkit master
# eggs = PyPDF
#
"""


def generate_appserver_cfg(args, indent=0):
    if not os.path.exists('appserver.cfg') or args.force_appserver_cfg:
        echo("Generating appserver.cfg: ", indent=indent, end='')
        appserver_cfg_content = APPSERVER_CFG_TEMPLATE.format(**args.__dict__)
        appserver_cfg = open('appserver.cfg', mode='w')
        appserver_cfg.write(appserver_cfg_content)
        appserver_cfg.close()
        echo("Done", indent=0, color=Fore.GREEN)
    else:
        echo("Existing appserver.cfg untouched. Use --force-appserver-cfg to regenerate it.", indent, Fore.CYAN)
    return 0


def assert_buildout_cfg_files(args, indent=0):
    """
    Check every required buildout cfg files exists and
    create missing ones
    """
    echo("Checking buildout.cfg files", indent=indent)
    exit_code = generate_appserver_cfg(args, indent=indent+1)
    if exit_code:
        return exit_code

    exit_code = generate_buildout_cfg(args, indent=indent+1)
    return exit_code


def bootstrap_buildout(args, indent=0):
    """
    bootstrap a buildout.
    """
    echo("Bootstrapping buildout", indent=indent)

    if not args.password:
        args.password = args.username

    exit_code = assert_buildout_cfg_files(args, indent=indent+1)
    if exit_code:
        return exit_code

    # To get latest bootstrap.py use:
    #    wget https://raw.github.com/buildout/buildout/master/bootstrap/bootstrap.py
    # We download bootstrap.py as of 14/12/2014 commit = 88ad9f4 using
    # wget https://raw.githubusercontent.com/buildout/buildout/88ad9f41bfbb32330a8fd37326ab93a82a984ba1/bootstrap/bootstrap.py
    exit_code = pretty_execute("Downloading bootstrap.py",
                               ['wget', 'https://raw.githubusercontent.com/buildout/buildout/'
                                '88ad9f41bfbb32330a8fd37326ab93a82a984ba1/bootstrap/bootstrap.py'],
                               args, indent=indent+1)
    if exit_code:
        return exit_code

    exit_code = pretty_execute("Creating virtualenv",
                               ['virtualenv', 'py27', '--no-setuptools', '--no-site-packages'],
                               args, indent=indent+1)
    if exit_code:
        return exit_code

    # we want setuptools==14.1.1 and zc.buildout==2.3.1
    exit_code = pretty_execute("Bootstrapping buildout '%s'" % ('2.3.1',),
                               ['py27/bin/python', 'bootstrap.py', '--version=2.3.1'],
                               args, indent=indent+1)
    if exit_code:
        return exit_code

    exit_code = pretty_execute("Cleaning",
                               ['rm', 'bootstrap.py'],
                               args, indent=indent+1)
    if exit_code:
        return exit_code

    # by default Install pip to have a developer friendly virtualenv
    if not args.no_pip:
        echo("Installing pip in virtualenv (use --no-pip if you want a pure virtualenv)", indent+1)
        exit_code = pretty_execute("Downloading get-pip.py",
                                   ['wget', 'https://bootstrap.pypa.io/get-pip.py'],
                                   args, indent=indent+2)
        if exit_code:
            return exit_code

        # Note that as of 15/03/2015, get-pip.py do not allow to choose pip version to install.
        exit_code = pretty_execute("Running get-pip.py",
                                   ['py27/bin/python', 'get-pip.py'],
                                   args, indent=indent+2)
        if exit_code:
            return exit_code

        exit_code = pretty_execute("Deleting files",
                                   ['rm', 'get-pip.py'],
                                   args, indent=indent+1)
        if not args.no_bzr:
            exit_code = pretty_execute("Installing bzr 2.6 (use --no-bzr to prevent)",
                                       ['py27/bin/pip', 'install', 'bzr==2.6'],
                                       args, indent=indent+1)
            if exit_code:
                return exit_code

    return exit_code


def do_buildout(args, indent=0):
    msg = "Running appserver 'bin/buildout'"
    if args.no_buildout_output:
        msg += " (use --no-buildout-output to hide command output)"

    exit_code = pretty_execute(msg,
                               ['bin/buildout'],
                               args,
                               capture_output=args.no_buildout_output,
                               indent=indent)
    return exit_code


def install(args):
    """
    Install Odoo from an ikez Git repository
    :param args:
    :type args:
    :return:
    :rtype:
    """

    if not args.username:
        print "You must specify a PostgreSQL username and password that will be used by Odoo to connect to database."
        print "If this user does not exist, ikez will create it. But if this user exists with a password different "
        print "than the one provided, ikez will exit and you will have to re-launch with a valid password"
        sys.exit(1)

    # Gather answer to all questions
    if not System.postgresql_version:
        if not args.locale and System.system_name in ('debian', 'ubuntu',):  # TODO: Check for Linux, add a system_info to group all Linux distrib
            if not args.unattended:
                locale = raw_input("Enter the locale you want to install or leave blank to use '%s' ? " % System.current_locale)
                if locale:
                    args.locale = locale
            else:
                echo("ERROR: Postgresql is not installed and '--locale' parameter "
                     "is missing. Relaunch with --locale or remove --unattended.",
                     color=Fore.RED)
                sys.exit(1)

    echo("Installing Odoo server")

    # Install required system packages
    exit_code = system.install_system_dependencies(args, indent=1)
    if exit_code:
        return exit_code

    # Install PostgreSQL
    if not System.postgresql_version:
        exit_code = postgresql.install(args, indent=1)
        if exit_code:
            return exit_code

    if args.repository:
        exit_code = pretty_execute("Checking repository URL validity",
                                   ['git', 'ls-remote', args.repository],
                                   args, indent=1)
        if exit_code:
            return exit_code

        # Computing dest directory
        if not args.destination:
            args.destination = args.repository.split('/')[-1]
            # TODO: Remove .git extension

        if args.destination:
            if os.path.exists(args.destination):
                echo("ERROR: folder '%s' exists. Please remove it then relaunch ikez." % args.destination,
                     indent=1, color=Fore.RED)
                return 1
        exit_code = pretty_execute("Cloning repository '%s'" % args.repository,
                                   ['git', 'clone', args.repository, args.destination],
                                   args, indent=1)
        if exit_code:
            return exit_code

        echo("Changing current directory to '%s'" % args.destination, indent=1)
        try:
            os.chdir('./'+args.destination)
        except:
            echo("ERROR: Unable to change current directory to '%s'." % args.destination, indent=1, color=Fore.RED)
            return 1

    if not is_cwd_an_ikez_repo(args):
        print "ERROR: Current directory is not an ikez Odoo repository."
        return 1

    # assert db user exists
    exit_code = enforcing_odoo_server_database_user(args, indent=1)
    if exit_code:
        return exit_code

    if not System.virtualenv_version_ok:
        exit_code = system.install_virtualenv(args, indent=1)
        if exit_code:
            return exit_code

    #integrated in bootstrap_bildout        
    #exit_code = assert_buildout_cfg_files(args, indent=1)
    #if exit_code:
    #    return exit_code

    if not os.path.exists('bin/buildout'):
        exit_code = bootstrap_buildout(args, indent=1)
        if exit_code:
            return exit_code

    exit_code = do_buildout(args, indent=1)

    return exit_code


###########
#
# reset command
#
def reset(args):
    echo("Removing all buildout generated items...")
    echo("Note that the ./downloads directory is not removed to avoid re-downloading openerp.",
         indent=1, color=Fore.CYAN)

    exit_code = pretty_execute("Deleting buildout files",
                               ['rm', '-rf', '.installed.cfg', 'bin/', 'develop-eggs/', 'eggs/', 'etc/', 'py27/'],
                               args=args, indent=1)
    return exit_code


def process_odoo_command(args):
    return eval("%s(args)" % args.command.replace('-','_'))
