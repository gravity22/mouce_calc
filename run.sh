#!/bin/sh

if [ $# -eq 0 ] ; then
    echo "Init Normal Mode"
    python -m mouse_calc
    exit 0
fi


if [ $# -eq 1 ] ; then
    echo "hogehoge"
fi
