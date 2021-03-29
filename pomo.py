#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""Configurable pomodoro technique aid.

Usage:
    pomo
    pomo list
    pomo set <property> <value>
    pomo --help             
    pomo --version

Options:
    -h --help               Show this screen
    --version               Display this program's version.
"""

import re
import time
from internal.docopt import docopt
from internal.config import get_configuration
from internal.timekeep import count_seconds, human_time_interval
from internal.editor import get_input_from_editor


TIME_INTERVAL_RE = re.compile(
    r'^\s*(\d+(?:\.\d+)?)\s?(h(?:ours?)?|m(?:inutes?)?|s(?:econds?)?)?\s*$', re.IGNORECASE)


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
        type_ = config['config'][prop]['type']
        new_value = arguments['<value>']
        if type_ == 'time':
            matches = TIME_INTERVAL_RE.match(new_value) 
            if matches is None:
                print(f'"{prop}" is expected to be time, but "{new_value}" '
                       'could not be read as time. Expected number followed '
                       'by "seconds", "minutes", "hours", "s", "m" or "h".')
                exit(1)
            new_value = float(matches.group(1))
            unit = matches.group(2)
            if unit.startswith('m'):
                new_value *= 60 
            elif unit.startswith('h'):
                new_value *= 3600
            new_value = int(new_value)
        elif type_ == 'exe':
            new_value = os.path.realpath(new_value)
            if not os.path.exists(new_value):
                print(f'"{prop}" is expected to point to an executable, '
                        f'but "{new_value}" does not exist.')
                exit(1)
            if not os.access(new_value, os.X_OK):
                print(f'"{prop}" is expected to point to an executable, '
                        f'but "{new_value}" is not an executable.')
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


def _run():
    with get_configuration() as config:
        editor_exe = config['config']['editor']['value']
        pomodoro = int(config['config']['pomodoro']['value'])
        short = int(config['config']['short']['value'])
        long_ = int(config['config']['long']['value'])

    # Get tasks
    empty_text = ('# Write your tasks separated by a blank line.\n'
        '# Lines starting with a # will be ignored.\n'
        '# Once you\'re done, exit the editor.')
    tasks_input = get_input_from_editor(empty_text, editor_exe)
    tasks = map(lambda task: task.strip(), tasks_input.split('\n\n'))
    tasks = filter(lambda task: task, tasks)
    tasks = map(lambda task: ' '.join(x.strip() for x in task.split('\n') if not x.startswith('#')), tasks)
    tasks = filter(lambda task: task, tasks)
    tasks = list(tasks)
    
    # Abort
    if len(tasks) == 0:
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
            print(f'Pomodoro #{pomodoro_count+1} starting!')
            count_seconds(pomodoro)

            try:
                checkmarks = '✓'*((pomodoro_count%4) + 1)
                print(f'{checkmarks} Done!')
            except UnicodeEncodeError:
                print('Done!')

            if (pomodoro_count%4) == 0:
                try:
                    print('⏲️ Take a long break!')
                except UnicodeEncodeError:
                    print('Take a long break!')
                count_seconds(long_)
            else:
                try:
                    print('⏲️ Take a short break!')
                except UnicodeEncodeError:
                    print('Take a short break!')
                count_seconds(short)
    except KeyboardInterrupt:
        pass

    # Give statistics
    work_time = time.time() - start_time
    print('\n')
    print('Good work!')
    print('Your tasks were:')
    print('\n'.join(f'  - {task}' for i, task in enumerate(tasks)))
    print(f'You worked for {human_time_interval(work_time)}.')
    print(f'You worked through {pomodoro_count} pomodoros.')
    print('See you next time!')
    exit(0)


if __name__ == '__main__':
    arguments = docopt(__doc__, version="pomo 0.1")

    if arguments['list']:
        _list_properties()
        exit(0)

    if arguments['set']:
        _edit_mode(arguments)
        exit(0)
    
    _run()

