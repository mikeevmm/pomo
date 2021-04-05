#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""Configurable pomodoro technique aid.

Usage:
    pomo
    pomo timer
    pomo list
    pomo set <property> <value>
    pomo reset <property>
    pomo --help             
    pomo --man
    pomo --version

Options:
    -h --help               Show this screen
    --man                   Show the README.
    --version               Display this program's version.
"""

import re
import time
import os
import threading
from internal.docopt import docopt
from internal.playsound import playsound
from internal.config import get_configuration, get_default_configuration
from internal.timekeep import countdown_seconds, human_time_interval
from internal.editor import get_input_from_editor
from internal.notify import notify_and_print


TIME_INTERVAL_RE = re.compile(
    r'^\s*(\d+(?:\.\d+)?)\s?(h(?:ours?)?|m(?:inutes?)?|s(?:econds?)?)?\s*$', re.IGNORECASE)


def _print_readme():
    readme_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'README.md')
    if not os.path.exists(readme_path):
        print('README not found.')
        exit(1)
    with open(readme_path, 'r') as readme_file:
        print(readme_file.read())


def _list_properties():
    with get_configuration() as config:
        for prop in config['config']:
            description = config['config'][prop]['name']
            value = config['config'][prop]['value']
            print(f'- {prop}')
            print(f'  {description}')
            print(f'  Current value: {value}')


def _edit_mode(arguments):
    with get_configuration() as config:
        # Check if property exists
        prop = arguments['<property>']
        if prop not in config['config']:
            print(f'{prop} is not a recognized property. '
                  'Call `pomo list` for a list of configuration properties '
                  'that can be set.')
            exit(1)
        
        # Check if value can be coerced into correct type
        # Optional values ('<type>?') are checked if the given value
        #  is truthy
        type_ = config['config'][prop]['type']
        new_value = arguments['<value>']
        optional = type_.endswith('?')
        if (not optional) or new_value:
            def warn_if_optional():
                if optional:
                    print('This property is optional, and can be disabled by '
                            'setting it to an empty value (\'\').')

            if type_.startswith('time'):
                matches = TIME_INTERVAL_RE.match(new_value) 
                if matches is None:
                    print(f'"{prop}" is expected to be time, but "{new_value}" '
                          'could not be read as time. Expected number followed '
                          'by "seconds", "minutes", "hours", "s", "m" or "h".')
                    warn_if_optional()
                    exit(1)
                new_value = float(matches.group(1))
                unit = matches.group(2)
                if unit is not None:
                    if unit.startswith('m'):
                        new_value *= 60 
                    elif unit.startswith('h'):
                        new_value *= 3600
                new_value = int(new_value)
            elif type_.startswith('exe'):
                new_value = os.path.realpath(new_value)
                if not os.path.exists(new_value):
                    print(f'"{prop}" is expected to point to an executable, '
                          f'but "{new_value}" does not exist.')
                    warn_if_optional()
                    exit(1)
                if not os.access(new_value, os.X_OK):
                    print(f'"{prop}" is expected to point to an executable, '
                          f'but "{new_value}" is not an executable.')
                    warn_if_optional()
                    exit(1)
            elif type_.startswith('file'):
                new_value = os.path.realpath(new_value)
                if not os.path.exists(new_value):
                    print(f'"{prop}" is expected to point to a file, '
                          f'but "{new_value}" does not exist.')
                    warn_if_optional()
                    exit(1)
            else:
                raise Exception(f'Type "{type_}" not implemented!')
        
        # Set the value
        prev_value = config['config'][prop]['value']
        config['config'][prop]['value'] = new_value
        
        # User feedback
        try:
            print(f'"{prop}": "{prev_value}" → "{new_value}"')
        except UnicodeEncodeError:
            print(f'"{prop}": "{prev_value}" -> "{new_value}"')


def _reset_mode(args):
    to_reset = args['<property>']
    default_config = get_default_configuration()
    with get_configuration() as config:
        if to_reset not in config['config']:
            print(f'Property \'{to_reset}\' does not exist.\n'
                    'Call `pomo list` to see a list of the existing '
                    'properties and their descriptions.')
            exit(1)
        old_value = config['config'][to_reset]['value']
        new_value = default_config['config'][to_reset]['value']
        config['config'][to_reset]['value'] = new_value

    # User feedback
    try:
        print(f'"{to_reset}": "{old_value}" → "{new_value}"')
    except UnicodeEncodeError:
        print(f'"{to_reset}": "{old_value}" -> "{new_value}"')


def _run(with_tasks):
    with get_configuration() as config:
        editor_exe = config['config']['editor']['value']
        pomodoro = int(config['config']['pomodoro']['value'])
        short = int(config['config']['short']['value'])
        long_ = int(config['config']['long']['value'])

        # Backwards compatibility: if property sound does not
        # exist, set it to the default value
        if 'sound' not in config['config']:
            config['config']['sound'] = \
                    get_default_configuration()['config']['sound']
        sound = config['config']['sound']['value']
        play_sound = (sound and os.path.exists(sound))

        if 'break-sound' not in config['config']:
            config['config']['break-sound'] = \
                    get_default_configuration()['config']['break-sound']
        break_sound = config['config']['break-sound']['value']
        play_break_sound = (break_sound and os.path.exists(break_sound))

    if with_tasks:
        # Check that editor is valid at runtime
        if not (os.path.exists(editor_exe) and os.access(editor_exe, os.X_OK)):
            editor_exe = os.environ['EDITOR']
            if not editor_exe or \
                    not (os.path.exists(editor_exe) and os.access(editor_exe, os.X_OK)):
                editor_exe = '/bin/nano'
                if not (os.path.exists(editor_exe)
                        and os.access(editor_exe, os.X_OK)):
                    print('Configured editor does not exist, $EDITOR is '
                          'not set and could not fall back to /bin/nano.\n'
                          'Please set your text editor using '
                          '`pomo set editor <editor path>')
                    exit(1)
                else:
                    print('Warning: configured editor does not exist and '
                          '$EDITOR is not set. Falling back to /bin/nano.')
                    with get_configuration() as config:
                        config['config']['editor']['value'] = '/bin/nano'
            else:
                print('Warning: configured editor does not exist. '
                      f'Falling back to $EDITOR ("{os.environ["EDITOR"]}").')
                with get_configuration() as config:
                    config['config']['editor']['value'] = os.environ['EDITOR']

        # Get tasks
        empty_text = ('# Write your tasks separated by a blank line.\n'
                      '# Lines starting with a # will be ignored.\n'
                      '# Once you\'re done, exit the editor.')
        tasks_input = get_input_from_editor(empty_text, editor_exe)
        tasks = map(lambda task: task.strip(), tasks_input.split('\n\n'))
        tasks = filter(lambda task: task, tasks)
        tasks = map(lambda task: ' '.join(
            x.strip() for x in task.split('\n') if not x.startswith('#')),
            tasks)
        tasks = filter(lambda task: task, tasks)
        tasks = list(tasks)
        
        # Abort
        if len(tasks) == 0:
            print('No tasks given, exiting')
            exit(0)

        # User feedback
        print('Ok, your tasks are:')
        print('\n'.join(f'  [{i}]: {task}' for i, task in enumerate(tasks)))
        print('')

    # Start pomodoro routine
    start_time = time.time()
    pomodoro_count = 0
    try:
        while True:
            notify_and_print(f'Pomodoro #{pomodoro_count+1} starting!')
            countdown_seconds(pomodoro)

            try:
                checkmarks = '✓'*((pomodoro_count % 4) + 1)
                notify_and_print(f'{checkmarks} Done!')
            except UnicodeEncodeError:
                notify_and_print('Done!')

            if play_sound:
                threading.Thread(target=playsound, args=(sound,)).start()

            if ((pomodoro_count+1) % 4) == 0:
                try:
                    notify_and_print('⏲️ Take a long break!')
                except UnicodeEncodeError:
                    notify_and_print('Take a long break!')
                countdown_seconds(long_)
            else:
                try:
                    notify_and_print('⏲️ Take a short break!')
                except UnicodeEncodeError:
                    notify_and_print('Take a short break!')
                countdown_seconds(short)

            if play_break_sound:
                threading.Thread(target=playsound, args=(break_sound,)).start()

            pomodoro_count += 1
    except KeyboardInterrupt:
        pass

    # Give statistics
    work_time = time.time() - start_time
    print('\n')
    print('Good work!')
    if with_tasks:
        print('Your tasks were:')
        print('\n'.join(f'  - {task}' for i, task in enumerate(tasks)))
    print(f'You worked for {human_time_interval(work_time)}.')
    print(f'You worked through {pomodoro_count} pomodoros.')
    print('See you next time!')
    exit(0)


if __name__ == '__main__':
    args = docopt(__doc__, version="pomo 0.9")

    if args['--man']:
        _print_readme()
        exit(0)

    if args['list']:
        _list_properties()
        exit(0)

    if args['set']:
        _edit_mode(args)
        exit(0)

    if args['reset']:
        _reset_mode(args)
        exit(0)
    
    _run(not args['timer'])
