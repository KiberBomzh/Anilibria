#!/usr/bin/env bash

am start\
 -n com.mxtech.videoplayer.pro/.ActivityScreen\
 -a android.intent.action.VIEW\
 -d "$1"\
 -e "title"  "$2"
exit
