#!/usr/bin/python

# Converts iperf3 json on the server output files to csv printouts


import json
from pprint import pprint


print "hilog ================="

filename = 'serv_hilog'

with open(filename) as fp:
    a = json.load(fp)

#pprint(a)

for interval in a['intervals']:
    stream = interval['streams'][0]
    print '%s, %s, %s, %s' % (stream['end'], stream['bits_per_second'], stream['bytes'], stream['seconds'])



print "lolog ===================="



filename = 'serv_lolog'

with open(filename) as fp:
    a = json.load(fp)

#pprint(a)

for interval in a['intervals']:
    stream = interval['streams'][0]
    print '%s, %s, %s, %s' % (stream['end'], stream['bits_per_second'], stream['bytes'], stream['seconds'])

   
