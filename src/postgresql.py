# coding: utf-8
import sys
import os
from colorama import Fore
from system_info import System
import subprocess
import system
from utils import echo, pretty_execute


def exec_psql_command(msg, sql_command, database='postgres', sudo=False, args=None, indent=0, env=None):

    if System.system_name in ( 'debian', 'ubuntu',):
        command = [ 'sudo', 'su', 'postgres', '-c',
            'psql %s -tAc "%s"' % (database, sql_command)
        ]
    elif System.system_name == 'darwin':
        command = ['psql', database, '-tAc', sql_command]

    exit_code, output = pretty_execute(msg, command, args, indent=indent, return_output=True, env=env)
    return exit_code, output

def exec_psql_user_command(msg, username, password, sql_command, host='localhost', database='postgres', args=None, indent=0):
    if System.system_name in ('debian', 'ubuntu', 'darwin'):
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        command = [
            'psql', '--host=%s' % host, '--username=%s' % username, database, '-c',
            "%s" % sql_command
        ]
    else:
        raise NotImplemented("exec_psql_user_command() is not implemented for %s" % System.system_name)

    exit_code, output = pretty_execute(msg, command, args, indent=indent, return_output=True, env=env)
    return exit_code, output


def pg_test_user_connection(username, password, host, args=None, indent=0):
    exit_code, output = exec_psql_user_command("Checking database connexion for user '%s'" % username, username, password,
                                               "select version();", host=host, args=args, indent=indent)
    return exit_code


def pg_user_exists(username, args=None, indent=0):
    """
    Check whether a postgres user exists.
    :param username:
    :type username: str
    :return: True if it exists or False
    :rtype: bool
    """

    if System.system_name in ('debian', 'ubuntu', 'darwin',):
        exit_code, nb_user = exec_psql_command("Check if user '%s' exists" % username,
                                               "SELECT COUNT(*) FROM pg_roles WHERE rolname='%s';" % username,
                                               args=args, indent=indent)
    else:
        raise NotImplementedError()
    return True if int(nb_user)>0 else False

def pg_set_password(username, password, args, indent=0):
    """
    Set a user's password.
    :param username:
    :type username: str
    :param password:
    :type password: str
    :return: # TODO: what
    :rtype: bool
    """
    set_password_cmd = ['psql', 'postgres', '-tAc', "SELECT COUNT(*) FROM pg_roles WHERE rolname='%s';" % username]

    # This works on OSX or Ubuntu
    if System.system_name in ('debian', 'ubuntu', 'darwin',):
        set_password_cmd = "ALTER USER %s WITH ENCRYPTED PASSWORD '%s';" % (username, password,)
        exit_code, output = exec_psql_command("Defining user '%s' password to '%s'" % (username, password,),
                                              set_password_cmd,
                                              indent=indent, args=args)
    else:
        raise NotImplemented("pg_set_password() is not implemented for %s" % System.system_name)
    return exit_code

def pg_create_user(username, password, args, indent=0):
    """
    Create a postgres user.
    :param username:
    :type username: str
    :param password:
    :type password: str
    :return:
    :rtype: bool
    """
    if System.system_name in ('debian', 'ubuntu', 'darwin'):
        sql_command = "CREATE USER %s WITH SUPERUSER CREATEROLE CREATEDB REPLICATION LOGIN ENCRYPTED PASSWORD '%s';" % (username, password,)
        exit_code, _ = exec_psql_command("Create user '%s'" % username,
                                         sql_command,
                                         args=args, indent=indent+1)
        return exit_code
    raise NotImplementedError()

def pg_create_user_database(username, args=None, indent=0):
    """
    Create a database named after user so that we can launch psql without any error.
    :param username:
    :type username: str
    :param password:
    :type password: str
    :return:
    :rtype: bool
    """
    if System.system_name in ('debian', 'ubuntu', 'darwin'):
        exit_code, result = exec_psql_command("Check whether a database named '%s' exists" %  username,
                                              "SELECT COUNT(*) FROM pg_database WHERE datname='%s';" % username, args=args, indent=indent)
        if exit_code:
            return exit_code

        if int(result) == 1:
            # TODO: Check dbowner
            echo("WARNING: A database named '%s' already exists. Check owner." % username, indent=indent)
            return 126

        exit_code, result = exec_psql_command("Create database '%s'" % username,
                                              "CREATE DATABASE %s WITH OWNER=%s ;" % (username, username,), args=args, indent=indent+1)
        return exit_code


def createuser(args, indent=0):
    """
    Create a postgresql user or update his password.
    :param args:
    :type args: Namespace
    :return:
    :rtype:
    """
    assert System.postgresql_version, "PostgreSQL server is not installed"

    args.username = args.username or os.environ['USER']

    if pg_user_exists(args.username, args, indent=indent+1):
        echo("User '%s' already exists."  % args.username, indent=indent+1)

        if args.password:
            echo("Resetting user '%s' password with '%s'." % (args.username, args.password,), indent=indent+1)
            exit_code = pg_set_password(args.username, args.password, args=args, indent=indent+1)
            if exit_code:
                return exit_code
        else:
            echo("No password specified. Nothing done !", indent=indent+1)
    else:
        args.password = args.password or args.username
        exit_code = pg_create_user(args.username, args.password, args=args, indent=indent+1)
        if exit_code:
            return exit_code

    # We create a database named after user so that we can launch psql without any error
    exit_code = pg_create_user_database(args.username, args=args, indent=indent+1)
    return exit_code


def postgresql_install_debian(args, indent=0):

    # argument --locale is required for odoo install but we suppose
    if args.locale:
        exit_code = system.set_locale_ubuntu(args.locale, args, indent=indent)
        if exit_code:
            return exit_code

    if System.system_name == 'debian' and System.system_major_version == '8':
        packages_list = ['postgresql-9.4', 'postgresql-contrib-9.4']
    else:
        packages_list = ['postgresql', 'postgresql-contrib']

    # let's install it
    exit_code = system.install_packages_debian(packages_list, args=args, indent=indent)
    return exit_code


POSTGRESQL_DEFAULT_PATH = '/Applications/Postgres.app/Contents/Versions/9.3/bin'

def add_postgres_to_system_path(args, indent=0):
    bash_profile_content = """# ikez: add Postgres.app binary to system PATH
export PATH=%s:$PATH
""" % POSTGRESQL_DEFAULT_PATH
    bash_profile_path = os.path.expanduser('~/.bash_profile')

    echo("Postgres.app bin folder added to .bash_profile", indent, color=Fore.GREEN)
    bash_profile = open(bash_profile_path, mode='a')
    bash_profile.write(bash_profile_content)
    bash_profile.close()

    #TODO: search for the string above in the file and prompt to relaunch a new session if it is found


def postgresql_install_darwin(args, indent=0):
    if args.locale:
        exit_code = system.set_locale_darwin(args.locale, args, indent=indent)
        if exit_code:
            return exit_code

    if not os.path.exists(POSTGRESQL_DEFAULT_PATH):
        echo("PostgreSQL database automated installation is not supported on Darwin.", color=Fore.CYAN)
        echo("Today, ikez recommended way of installing PostgreSQL is to use http://postgresapp.com :", color=Fore.CYAN)
        echo("  - Open https://github.com/PostgresApp/PostgresApp/releases/ in your browser", color=Fore.CYAN)
        echo("  - Download the last version in the "+Fore.RED+"9.3 serie.", color=Fore.CYAN)
        echo("  - Unzip the file, launch it,", color=Fore.CYAN)
        echo("  - Click on the Move button, when asked whether you want to \"Move to Applications folder ?\"", color=Fore.CYAN)
        return 126

    if POSTGRESQL_DEFAULT_PATH not in os.environ['PATH'].split(':'):
        echo("Postgres.app exists but psql is not on system path.", indent=indent, color=Fore.CYAN)
        add_postgres_to_system_path(args, indent=indent)
        echo("Now, you must reopen a new Terminal tab for the change to be effective.", indent=indent, color=Fore.RED)
        return 126


def install(args, indent=0):
    """
    Install postgresql server
    :param args:
    :type args:
    :return:
    :rtype:
    """
    echo("Installing PostgreSQL Server", indent=indent)

    if System.postgresql_version:
        echo("PostgreSQL server '%s' already installed with locale '%s'." % (System.postgresql_version, System.current_locale,),
             indent=indent+1, color=Fore.GREEN)
        return 0


    if System.system_name == 'darwin':
        return postgresql_install_darwin(args, indent=indent+1)

    elif System.system_name in ('debian', 'ubuntu',):
        return postgresql_install_debian(args, indent=indent+1)
    else:
        raise NotImplementedError("Postgresql installation is not supported on '%s'." % System.system_name)

def backup(args, indent):
    # TODO: implement this
    # git describe --always --tag
    # socket.gethostname
    #
    #local_backup(database, backup_file_name=None):
    #""":database - Backup database and put backup file into muppy directory using a muppy generated backup name"""
    #env_backup = (env.user, env.password,)
    #env.user, env.password = env.adm_user, env.adm_password

    #if not database:
    #    print red("ERROR: missing required database parameter.")
    #    exit(128)

    #if not backup_file_name:
    #    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    #    hostname = get_local_hostname()
    #    local('mkdir -p backups/%s' % hostname)
    #    backup_file_name = os.path.join('backups/%s' % hostname, "%s__%s__%s.pg_dump" % (timestamp, database, hostname,))
    #
    #backup_command_line = "export PGPASSWORD='%s' && pg_dump -Fc -h %s -U %s -f%s %s" % ( env.db_password, env.db_host, env.db_user, backup_file_name, database,)
    #local(backup_command_line)
    return


def process_postgresql_command(args):
    return eval("%s(args)" % args.command)
