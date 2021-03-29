#!/bin/bash

echo "Removing pomo link..."
if rm "$HOME/bin/pomo"; then
    echo -e "\033[32mDone.\033[0m"
else
    echo "Something went wrong."
fi
