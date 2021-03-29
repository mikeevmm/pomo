#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from time import sleep

_START_CHAR = '['
_START_CHAR_ALT = '['
_FULL_CHAR = '█'
_FULL_CHAR_ALT = '*'
_THREE_CHAR = '▆'
_THREE_CHAR_ALT = '+'
_TWO_CHAR = '▄'
_TWO_CHAR_ALT = '-'
_ONE_CHAR = '▁'
_ONE_CHAR_ALT = '.'
_EMPTY_CHAR = ' '
_EMPTY_CHAR_ALT = ' '
_END_CHAR = ']'
_END_CHAR_ALT = ']'


def _build_bar(fill, width, start_char, full_char, three_char, two_char,
        one_char, empty_char, end_char):
    full_count = int(fill*(width-2))
    remainder = (fill*(width-2))%1. 

    remainder_char = ''
    if remainder > 0.:
        if remainder < .25:
            remainder_char = empty_char
        elif remainder < .5:
            remainder_char = one_char
        elif remainder < .75:
            remainder_char = two_char
        elif remainder < 1.:
            remainder_char = three_char

    total_count = full_count if remainder == 0. else full_count + 1
    return start_char + full_count*full_char + remainder_char + \
            (width-2-total_count)*empty_char + end_char


def countdown_seconds(time, width=50, update_freq=8):
    last_width = 0
    for moment in range((time*update_freq)+1):
        second = moment/update_freq
        fill = 1. - second/time
        unicode_str = _build_bar(fill, width, _START_CHAR, _FULL_CHAR,
                        _THREE_CHAR, _TWO_CHAR, _ONE_CHAR, _EMPTY_CHAR,
                        _END_CHAR)
        unit_str = 'seconds' if int(second) > 1 else 'second'
        explicit_time = f' [{time - int(second)} {unit_str} left]'
        end = '\n' if int(second) == time else '\r'

        try:
            final_str = unicode_str + explicit_time
            print(final_str.ljust(last_width), end=end)
        except UnicodeEncodeError:
            ascii_str = _build_bar(fill, width, _START_CHAR_ALT, _FULL_CHAR_ALT,
                            _THREE_CHAR_ALT, _TWO_CHAR_ALT, _ONE_CHAR_ALT,
                            _EMPTY_CHAR_ALT, _END_CHAR_ALT)
            final_str = ascii_str + explicit_time
            print(final_str.ljust(last_width), end=end)
        last_width = len(final_str)
        sleep(1/update_freq)


def human_time_interval(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)
