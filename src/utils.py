# coding: utf-8
from __future__ import print_function
import subprocess
import sys
from colorama import Fore, Back


def execute(command, capture_output=False):
    """

    :param command: command a as parameter array (see subprocess call())
    :type command: list
    :return: (exit_code, output,)
    :rtype: tuple
    """
    if capture_output:
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            return (e.returncode, e.output,)
        except OSError as e:
            if e.errno == 2:
                return 1, "ERROR: '%s' command cannot be found."
            raise e
        else:
            return (0, output,)

    # we use call
    exit_code = subprocess.call(command)
    return (exit_code, '',)


# TODO: define this as a global setting define indent step (4 here)
INDENT_STEP = '    '
DRYRUN_TEMPLATE = Fore.RED+"Dryrun ===> "+Fore.RESET

def pretty_execute(message, command, args, capture_output=True, indent=0, return_output=False, env=None):
    """

    :param message: message to display to user
    :type message: str
    :param command: command to launch
    :type command: list
    :param args: ikez command line arguments
    :type args: argparse.Namespace
    :param capture_output: If True, use subprocess.check_output() and
    :type capture_output: bool
    :param indent:
    :type indent: int
    :param return_output: If True, output is not displayed but returned.
    :type return_output: bool
    :param env: environment dict to use
    :type env: dict
    :return: int or tuple
    :rtype: int or (int, str,)
    """
    if return_output and not capture_output:
        echo("INTERNAL ERROR: You can't call pretty_execute() with 'return_output and not capture_output'.", indent=indent, color=Fore.RED)

    indent_text = INDENT_STEP * indent

    training_text = ""
    if args.training:
        training_text = " with '%s%s%s'" % (Fore.MAGENTA, ' '.join(command), Fore.RESET)

    dryrun_text = ""
    if args.dryrun:
        dryrun_text = DRYRUN_TEMPLATE

    if capture_output:
        print("%s%s%s%s: " % (indent_text, dryrun_text, message, training_text), end='')
        sys.stdout.flush()  # TODO: Make it run when redirecting output
        try:
            if not args.dryrun:
                output = subprocess.check_output(command, stderr=subprocess.STDOUT, env=env)
        except subprocess.CalledProcessError as e:
            print(Fore.RED + "FAILED"+ Fore.RESET)
            if not return_output:
                print(Fore.RED + "=====(Error for '%s')==>>>" % ' '.join(command), Fore.RESET)
                print(e.output)
                print(Fore.RED + "<<<==(Error for '%s')=====" % ' '.join(command), Fore.RESET)
            return (e.returncode, e.output,) if return_output else e.returncode
        except OSError as e:
            if e.errno == 2:
                print("FAILED")
                print("%sERROR: '%s' command cannot be found." % (indent_text, command[0],))
                return (1, e.output,) if return_output else 1
            raise e

        print(Fore.GREEN+"Done."+Fore.RESET)
        return (0, output,) if return_output else 0

    # we use call
    print("%s%s:" % (indent_text, message,))
    print(Fore.MAGENTA + "======( Output for '%s' )===>>>" % ' '.join(command), Fore.RESET)
    exit_code = subprocess.call(command, env=env)
    print(Fore.MAGENTA + "<<<===( Output for '%s' )======" % ' '.join(command), Fore.RESET)

    return exit_code


def echo_color_set(color):
    print(color)
    return

def echo_color_reset():
    print(Back.RESET + Fore.RESET)
    return

def echo(msg='', indent=0, color=None, end='\n'):
    if not color:
        color_start = ''
        color_reset = ''
    else:
        color_start = color
        color_reset = Back.RESET + Fore.RESET

    print("%s%s%s%s" % (color_start, '    ' * indent, msg, color_reset,), end=end)
    return

def prompt(msg='', indent=0, color=None):
    if not color:
        color_start = ''
        color_reset = ''
    else:
        color_start = color
        color_reset = Back.RESET + Fore.RESET
    return raw_input("%s%s%s%s" % (color_start, '    '*indent, msg, color_reset,))
