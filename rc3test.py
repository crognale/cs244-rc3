#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import lg
from mininet.link import TCLink
from mininet.util import pmonitor
from mininet.cli import CLI
from time import time
from signal import SIGINT
import subprocess

# Actual experiment was 10Gbps and 1Gbps with an RTT of 20ms.
# We reduce the link speed and increase the latency to maintain
# the same Bandwidth-Delay Product

LINK_BW_1 = 100 # 100Mbps
LINK_BW_2 = 10 # 10Mbps

#DELAY = '500ms' # 0.5s, RTT=2s
DELAY = '20ms' # TODO remove (test)

class RC3Topo(Topo):	

    def __init__(self, bandwidth):

        #Initialize Topology
        Topo.__init__(self)

        # Add hosts and switch
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        switch = self.addSwitch('s1')

        # Add links
        self.addLink(h1, switch, bw=bandwidth, delay=DELAY, use_htb=True)
        self.addLink(switch, h2, bw=bandwidth, delay=DELAY, use_htb=True)


def addPrioQdisc(node, devStr):
#    node.cmdPrint('tc qdisc add dev', devStr,
#            'parent 10:1 handle 15:0 prio bands 8 priomap 0 1 2 3 4 5 6 7 7 7 7 7 7 7 7 7')
    node.cmdPrint('tc qdisc add dev', devStr,
            'parent 10:1 handle 15:0 prio bands 8 priomap 0 1 2 3 4 5 6 7 7 7 7 7 7 7 7 7')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x00 0xff flowid 15:1')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x04 0xff flowid 15:2')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x08 0xff flowid 15:3')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x0c 0xff flowid 15:4')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x10 0xff flowid 15:5')

     #node.cmdPrint('tc qdisc show')
    #CLI(net)

    #CLI(net)

    #node.cmdPrint('tc class add dev', devStr, 'parent 10:1 classid 15:1 htb rate 100kbps ceil 100kbps') 
#    node.cmdPrint('tc class add dev', devStr, 'parent 10:1 classid 15:1 htb rate 10kbps') 
#    node.cmdPrint('tc class add dev', devStr, 'parent 15:1 classid 15:100 htb rate 0kbps ceil 100kbps prio 0')
#    node.cmdPrint('tc class add dev', devStr, 'parent 15:1 classid 15:101 htb rate 0kbps ceil 100kbps prio 1')
#    node.cmdPrint('tc class add dev', devStr, 'parent 15:1 classid 15:102 htb rate 0kbps ceil 100kbps prio 2')
#    node.cmdPrint('tc qdisc show dev', devStr)
#    node.cmdPrint('tc class show dev', devStr)

#    node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x00 0xff flowid 15:100')
#    node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x04 0xff flowid 15:101')
#    node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x08 0xff flowid 15:102')

#   node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x0C 0xff flowid 1:10')
#   node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x10 0xff flowid 1:10')

    node.cmdPrint('tc -s class ls dev', devStr)


def rc3Test(bandwidth, flowLen):
    topo = RC3Topo(bandwidth)
    net = Mininet(topo, link=TCLink)
    net.start()


    print "Dumping node connections"
    dumpNodeConnections(net.hosts)

    h1, h2 = net.getNodeByName('h1', 'h2')

    print "Adding qdiscs"
    addPrioQdisc(h1, 'h1-eth0')
    addPrioQdisc(h2, 'h2-eth0')
    #TODO do we need this at the switch too?

    print "Testing bandwidth between 'h1' and 'h2'"
    h2.sendCmd('iperf -s')
    #result = h1.cmd('iperf -c', h2.IP(), '-n', flowLen)
    #print result
    '''
    print 'launching high priority iperf'
    h1.sendCmd('iperf -c', h2.IP(), '-n', flowLen, '-S 0x0 > highperf.txt')
    print 'launching low priority iperf'
    h1.sendCmd('iperf -c', h2.IP(), '-n', flowLen, '-S 0x4 > lowperf.txt')
    print 'lol'
    '''

    # Flow completion time tests
    popens = {}
    popens['server'] = h2.popen('./fcttest -s -p 5678 -g 1000000')
    for i in range(0,10):
      popens['client'] = h1.popen('./fcttest -c -a %s -p 5678 -g 1000000' % (h2.IP()), stdout = subprocess.PIPE)
      (out, err) = popens['client'].communicate()
      print "client:", out
    popens['server'].kill()

    print "RC3 mode ===================================================="
    popens['server'] = h2.popen('./fcttest -s -p 5678 -g 1000000 -r')
    for i in range(0,10):
      popens['client'] = h1.popen('./fcttest -c -a %s -p 5678 -g 1000000 -r' % (h2.IP()), stdout = subprocess.PIPE)
      (out, err) = popens['client'].communicate()
      print "client:", out
    popens['server'].kill()



    

    #endTime = time() + 40 #seconds
    #client_runs = 1
    #for perf, line in pmonitor(popens, timeoutms=100):
    #    print "boink"
    #    h1.cmdPrint('tc -s qdisc ls dev h1-eth0')
    #    if perf:
    #        print '<%s>: %s' % (perf, line)
    #    if time() >= endTime:
    #        print 'timeout'
    #        for p in popens.values():
    #            p.send_signal( SIGINT )
    #    if 'client' not in popens or popens['client'].poll() is None:
    #        print "is none"
    #        if client_runs < 10:
    #            popens['client'] = h1.popen('./fcttest -c -a %s -p 5678 -g 1000000' % (h2.IP()))
    #            client_runs += 1
    #        else:
    #            for p in popens.values():
    #                p.send_signal( SIGINT )
    #            break



    '''
    popens = {}
    print 'launching low priority iperf'
    popens['loperf'] = h1.popen('iperf -c %s -n %i -S 0x4 > loperf.txt' % (h2.IP(), flowLen))

    print 'launching high priority iperf'
    popens['hiperf'] = h1.popen('iperf -c %s -n %i -S 0x0 > hiperf.txt' % (h2.IP(), flowLen))
    endTime = time() + 40 #seconds
    for perf, line in pmonitor(popens, timeoutms=100):
    #    h1.cmdPrint('tc -s qdisc ls dev h1-eth0')
        if perf:
            print '<%s>: %s' % (perf, line)
        if time() >= endTime:
            print 'timeout'
            for p in popens.values():
                p.send_signal( SIGINT )
    '''
    net.stop()

if __name__ == '__main__':
    lg.setLogLevel('info')
    rc3Test(LINK_BW_1, 20000000)
