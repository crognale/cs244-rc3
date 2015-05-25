#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import lg
from mininet.link import TCLink
from mininet.util import pmonitor
from mininet.cli import CLI
from time import time
from time import sleep
from signal import SIGINT
import subprocess

# Actual experiment was 10Gbps and 1Gbps with an RTT of 20ms.
# We reduce the link speed and increase the latency to maintain
# the same Bandwidth-Delay Product

LINK_BW_1 = 100 # 100Mbps
LINK_BW_2 = 10 # 10Mbps

#DELAY = '500ms' # 0.5s, RTT=2s
DELAY = '2ms' # TODO remove (test)

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


def addPrioQdisc(node, devStr, bandwidth, delay):
    " delay should be a string like '10us', bandwidth is a number in Mbps "
#    node.cmdPrint('tc qdisc add dev', devStr,
#            'parent 10:1 handle 15:0 prio bands 8 priomap 0 1 2 3 4 5 6 7 7 7 7 7 7 7 7 7')

    node.cmdPrint('tc qdisc show dev', devStr)
    node.cmdPrint('tc class show dev', devStr)
    
    '''
    node.cmdPrint('tc qdisc add dev', devStr,
            'parent 10:1 handle 15:0 prio bands 8 priomap 0 1 2 3 4 5 6 7 7 7 7 7 7 7 7 7')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:1 handle 151: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:2 handle 152: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:3 handle 153: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:4 handle 154: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:5 handle 155: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:6 handle 156: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:7 handle 157: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:8 handle 158: pfifo')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x00 0xff flowid 15:1')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x04 0xff flowid 15:2')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x08 0xff flowid 15:3')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x0c 0xff flowid 15:4')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x10 0xff flowid 15:5')
    '''

    """
    #node.cmdPrint('tc qdisc add dev', devStr,
    #        'parent 10:1 handle 15:0 prio bands 8 priomap 0 1 2 3 4 5 6 7 7 7 7 7 7 7 7 7')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:1 handle 151: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:2 handle 152: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:3 handle 153: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:4 handle 154: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:5 handle 155: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:6 handle 156: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:7 handle 157: pfifo')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 10:8 handle 158: pfifo')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x00 0xff flowid 15:1')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x04 0xff flowid 15:2')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x08 0xff flowid 15:3')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x0c 0xff flowid 15:4')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x10 0xff flowid 15:5')
    """


    rate = "%fMbit" % bandwidth

    node.cmdPrint('tc qdisc del dev', devStr, 'root');

    node.cmdPrint('tc qdisc add dev', devStr, 'root handle 1: htb default 1')

    print "TODO: Set burst rates to match original?"

    node.cmdPrint('tc class add dev', devStr, 'classid 1:1 parent 1: htb rate', rate, 'ceil', rate)

    node.cmdPrint('tc qdisc add dev', devStr,
                   'parent 1:1 handle 15:0 prio bands 8 priomap 0 1 2 3 4 5 6 7 7 7 7 7 7 7 7 7')
 
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:1 handle 151: netem delay', delay, 'limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:2 handle 152: netem delay', delay, 'limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:3 handle 153: netem delay', delay, 'limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:4 handle 154: netem delay', delay, 'limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 15:5 handle 155: netem delay', delay, 'limit 1000')

    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x00 0xff flowid 15:1')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x04 0xff flowid 15:2')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x08 0xff flowid 15:3')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x0c 0xff flowid 15:4')
    node.cmdPrint('tc filter add dev', devStr, 'parent 15:0 protocol ip prio 10 u32 match ip tos 0x10 0xff flowid 15:5')



    """
    #Not-working layers of token buckets - doesn't balance properly
    rate = '100000Kbit'
    rate2 = '1bps' 

    node.cmdPrint('tc qdisc del dev', devStr, 'root');

    node.cmdPrint('tc qdisc add dev', devStr, 'root handle 1: htb default 1')

    node.cmdPrint('tc class add dev', devStr, 'classid 1:1 parent 1: htb rate', rate, 'ceil', rate)
    node.cmdPrint('tc class add dev', devStr, 'classid 1:10 parent 1:1 htb rate', rate2, 'ceil', rate, 'prio 1')
    node.cmdPrint('tc class add dev', devStr, 'classid 1:11 parent 1:1 htb rate', rate2, 'ceil', rate, 'prio 2')
    node.cmdPrint('tc class add dev', devStr, 'classid 1:12 parent 1:1 htb rate', rate2, 'ceil', rate, 'prio 3')
    node.cmdPrint('tc class add dev', devStr, 'classid 1:13 parent 1:1 htb rate', rate2, 'ceil', rate, 'prio 4')
    node.cmdPrint('tc class add dev', devStr, 'classid 1:14 parent 1:1 htb rate', rate2, 'ceil', rate, 'prio 5')

    node.cmdPrint('tc qdisc add dev', devStr, 'parent 1:10 handle 10: netem delay 2ms limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 1:11 handle 11: netem delay 2ms limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 1:12 handle 12: netem delay 2ms limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 1:13 handle 13: netem delay 2ms limit 1000')
    node.cmdPrint('tc qdisc add dev', devStr, 'parent 1:14 handle 14: netem delay 2ms limit 1000')

    node.cmdPrint('tc filter add dev', devStr, 'parent 1: protocol ip prio 10 u32 match ip tos 0x00 0xff flowid 1:10')
    node.cmdPrint('tc filter add dev', devStr, 'parent 1: protocol ip prio 10 u32 match ip tos 0x04 0xff flowid 1:11')
    node.cmdPrint('tc filter add dev', devStr, 'parent 1: protocol ip prio 10 u32 match ip tos 0x08 0xff flowid 1:12')
    node.cmdPrint('tc filter add dev', devStr, 'parent 1: protocol ip prio 10 u32 match ip tos 0x0c 0xff flowid 1:13')
    node.cmdPrint('tc filter add dev', devStr, 'parent 1: protocol ip prio 10 u32 match ip tos 0x10 0xff flowid 1:14')
    """ 


    # Direct iperf traffic to classid 10:1
    #tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip dport 5001 0xffff flowid 1:10
    #tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip sport 5001 0xffff flowid 1:10
    #tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip protocol 1 0xff flowid 1:11
    #tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip dport 80 0xffff flowid 1:11
    #tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip sport 80 0xffff flowid 1:11
    #echo filters added



     #node.cmdPrint('tc qdisc show')
    #CLI(net)

    #CLI(net)

    #node.cmdPrint('tc class add dev', devStr, 'parent 10:1 classid 15:1 htb rate 100kbps ceil 100kbps') 
#    node.cmdPrint('tc class add dev', devStr, 'parent 10:1 classid 15:1 htb rate 10kbps') 
#    node.cmdPrint('tc class add dev', devStr, 'parent 15:1 classid 15:100 htb rate 0kbps ceil 100kbps prio 0')
#    node.cmdPrint('tc class add dev', devStr, 'parent 15:1 classid 15:101 htb rate 0kbps ceil 100kbps prio 1')
#    node.cmdPrint('tc class add dev', devStr, 'parent 15:1 classid 15:102 htb rate 0kbps ceil 100kbps prio 2')
    node.cmdPrint('tc qdisc show dev', devStr)
    node.cmdPrint('tc class show dev', devStr)

#    node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x00 0xff flowid 15:100')
#    node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x04 0xff flowid 15:101')
#    node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x08 0xff flowid 15:102')

#   node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x0C 0xff flowid 1:10')
#   node.cmdPrint('tc filter add dev', devStr, 'parent 1:0 protocol ip prio 10 u32 match ip tos 0x10 0xff flowid 1:10')

    node.cmdPrint('tc -s class ls dev', devStr)


# skip = number of initial runs to not include in the results (total runs = skip + iterations)
def fct_test(net, skip = 3, size = 1024*1024, iterations = 10, use_rc3=False):
    results = []

    h1, h2 = net.getNodeByName('h1', 'h2')

    rc3_string = "-r" if use_rc3 else ""

    # Start server
    p_srv = h2.popen('./fcttest -s -p 5678 -g %d %s' % (size, rc3_string),
                     stdout = subprocess.PIPE, stderr = subprocess.PIPE)

    # Run the client iterations + skip times
    for i in range(0,iterations + skip):
      p_clt = h1.popen('./fcttest -c -a %s -p 5678 -g %d %s' % (h2.IP(), size, rc3_string),
                       stdout = subprocess.PIPE, stderr = subprocess.PIPE)
      (out, err) = p_clt.communicate()
      if err or p_clt.returncode != 0:
        print "[ERROR]: fcttest client error:", err
      else:
        skip_this = i < skip
        print "skip_this =", skip_this, ", use_rc3 =", use_rc3, ", size =", size, ", time (ms) =", float(out)
        if not skip_this: 
          results.append(float(out))

    # Kill the server
    if p_srv.poll() is None:
      p_srv.kill()
    else:
      (out, err) = p_srv.communicate()
      print "[ERROR]: fcttest error: %s" % err

    return results

def rc3Test(bandwidth, flowLen):
    topo = RC3Topo(bandwidth)
    net = Mininet(topo, link=TCLink)
    net.start()


    print "Dumping node connections"
    dumpNodeConnections(net.hosts)

    h1, h2 = net.getNodeByName('h1', 'h2')

    print "Adding qdiscs"
    addPrioQdisc(h1, 'h1-eth0', bandwidth, DELAY)
    addPrioQdisc(h2, 'h2-eth0', bandwidth, DELAY)
    #TODO do we need this at the switch too?

    #print "Testing bandwidth between 'h1' and 'h2'"
    #h2.sendCmd('iperf -s')
    #result = h1.cmd('iperf -c', h2.IP(), '-n', flowLen)
    #print result
    '''
    print 'launching high priority iperf'
    h1.sendCmd('iperf -c', h2.IP(), '-n', flowLen, '-S 0x0 > highperf.txt')
    print 'launching low priority iperf'
    h1.sendCmd('iperf -c', h2.IP(), '-n', flowLen, '-S 0x4 > lowperf.txt')
    print 'lol'
    '''

    #CLI(net)


    # Run two iperf streams of different priority. Use jsoniper.py to parse the server output
    ps1 = h2.popen('iperf3 -s -p 5001 -J > serv_lolog', shell=True);
    ps2 = h2.popen('iperf3 -s -p 5002 -J > serv_hilog', shell=True);
    pc1 = h1.popen('iperf3 -c %s -p 5001 -i 1 -t 35 -S 0x4 -J > lolog'%(h2.IP(),), shell=True);

    count = 0
    while (pc1.poll() is None) or (pc2.poll() is None):
      print "count: ", count, "=============================="
      count += 1
      h1.cmdPrint('tc -s class ls dev h1-eth0')
      sleep(1)
      if count == 10:
          pc2 = h1.popen('iperf3 -c %s -p 5002 -i 1 -t 10 -S 0x0 -J > hilog'%(h2.IP(),), shell=True);

    pc1.wait()
    pc2.wait()
    ps1.terminate()
    ps2.terminate()

#    # Flow completion time tests
#    results = fct_test(net, iterations=5, size=1024*1024, use_rc3=False)
#    print "results", results
#
#    print "RC3 mode ===================================================="
#    results = fct_test(net, iterations=5, size=1024*1024, use_rc3=True)
#    print "results", results


    '''
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
    '''


    

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
