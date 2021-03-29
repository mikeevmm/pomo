#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import tempfile
import os
from subprocess import call

def get_input_from_editor(initial_msg, editor_exe):
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tf:
        tf.write(initial_msg.encode('utf-8'))
        tf.flush()
        call([editor_exe, tf.name])

    with open(tf.name, 'r') as tf:
        edited_msg = tf.read()
    
    os.remove(tf.name)
    
    return edited_msg

