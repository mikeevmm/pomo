#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from subprocess import run, DEVNULL 

_enabled = \
    (run(['notify-send', '-v'], stdout=DEVNULL, stderr=DEVNULL).returncode == 0)

def notification(title, body=None):
    if not _enabled:
        return None
    if body is None:
        run(['notify-send', title])
    else:
        run(['notify-send', title, body])

def notify_and_print(text, *print_args, **print_kwargs):
    # NOTE: Print should come before the notification,
    # so that if a UnicodeEncodingError is raised, the
    # notification is never sent.
    print(text, *print_args, **print_kwargs)
    notification(text)
