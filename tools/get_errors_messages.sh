#! /bin/bash
#
# get_errors_messages.sh
# Copyright (C) 2015 pparissis <pavlos.parissis@booking.com>
#
# Distributed under terms of the MIT license.
#

cat src/dumpstats.c |awk -F'=' '{if (match($0,/appctx->ctx.cli.msg/) && match($2,/^ "/")) {sub(/\\n"/,"\"",$2");sub(/;$/,",",$2);print $2}}' |sort|uniq'
