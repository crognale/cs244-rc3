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
from figure15_helpers import *

# Actual experiment was 10Gbps and 1Gbps with an RTT of 20ms.
# We reduce the link speed and increase the latency to maintain
# the same Bandwidth-Delay Product

LINK_BW_1 = 100 # 100Mbps
LINK_BW_2 = 10 # 10Mbps

#DELAY = '500ms' # 0.5s, RTT=2s
DELAY = '1000ms' # TODO This is correct if delay only on host interfaces.

class RC3Topo(Topo):

    def __init__(self, bandwidth):

        #Initialize Topology
        Topo.__init__(self)

        # Add hosts and switch
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        switch = self.addSwitch('s1')

        # Add links. Note: Delay inserted by custom prio qdisc code
        self.addLink(h1, switch, bw=bandwidth, use_htb=True)
        self.addLink(switch, h2, bw=bandwidth, use_htb=True)

def addPrioQdisc(node, devStr, bandwidth, delay):
    '''Setup the HTB, prio qdisc, netem, etc.

    node: Network node, e.g. h1, h2, s1
    devStr: Device name string, e.g. 'h1-eth0'
    bandwidth: A number, representing amount of Mbps
    delay: a string, such as 10us
    '''

    print devStr, "Initial tc Configuration ==========================="
    node.cmdPrint('tc qdisc show dev', devStr)
    node.cmdPrint('tc class show dev', devStr)

    print devStr, "Setting tc Configuration ==========================="
    node.cmdPrint('tc qdisc del dev', devStr, 'root');
    node.cmdPrint('tc qdisc add dev', devStr, 'root handle 1: htb default 1')
    # TODO
    print "TODO: Set burst rates to match original?"
    rate = "%fMbit" % bandwidth
    node.cmdPrint('tc class add dev', devStr, 'classid 1:1 parent 1: htb rate',
                  rate, 'ceil', rate)
    node.cmdPrint('tc qdisc add dev', devStr,
                  'parent 1:1 handle 15:0 prio bands 8 '
                  'priomap 0 1 2 3 4 5 6 7 7 7 7 7 7 7 7 7')
    for i in range(1, 5+1):
        node.cmdPrint('tc qdisc add dev %s parent 15:%d handle 15%d:'
                      ' netem delay %s limit 1000' % (devStr, i, i, delay))
    for (i,tos) in zip(range(1, 5+1), ['0x00','0x04','0x08','0x0c','0x10']):
        node.cmdPrint('tc filter add dev %s parent 15:0 protocol ip'
                      ' prio 10 u32 match ip tos %s 0xff flowid 15:%d'
                      % (devStr, tos, i))

    print devStr, "Custom tc Configuration ============================"

    node.cmdPrint('tc qdisc show dev', devStr)
    node.cmdPrint('tc class show dev', devStr)
    node.cmdPrint('tc filter show dev', devStr, 'parent 15:0')
    node.cmdPrint('tc -s class ls dev', devStr)

def do_fct_tests(net, iterations, time_scale_factor, starter_data_function,
                 fig_file_name = None):
    '''Run a series of flow completion time tests, and make a bar chart.

    net: Mininet net object.
    iterations: Number of times to test FCT at a given setting, before
        taking mean and stddev.
    time_scale_factor: FCTs will be scaled by this amount, to normalize
        results. I.e. if link delay is scaled by 10, scale_factor should
        probably be 1/10.
    starter_data_function: The name of a function which will give a data
        structure for plotting. This is used to get the data from the paper
        figures 15(a) and 15(b). See figure15_helpers.py.
    fig_file_name: If specified, where to save the resulting plot.
    '''

    # Flow lengths for the flow completion times.
    flow_lengths = [1460, 7300, 14600, 73000, 146000, 730000, 1460000]

    # Start with the bar-graph data from the paper
    (data, flow_types, flow_type_colors, title) = starter_data_function()

    # Do flow-completion-time tests for each flow length,
    # using regular TCP and rc3, and add to graph data structure
    for flow_length in flow_lengths:
        for (rc3, flow_type) in [(False, 'Mininet Regular TCP'),
                                 (True,  'Mininet RC3')]:
            results = fct_test(net, iterations=iterations, size=flow_length,
                               use_rc3=rc3)
            print "results", results
            s = time_scale_factor * 0.001 # external scale and msecs to secs
            data[flow_length][flow_type] = {'mean'  : s * avg(results),
                                            'stddev': s * stddev(results)}

    plotBarClusers(data, flow_types, flow_type_colors, title, fig_file_name)

def fct_test(net, skip = 3, size = 1024*1024, iterations = 10, use_rc3=False):
    '''Run the fcttest multiple times, return list of times in milliseconds.

    net: Mininet net object.
    skip: The number of initial tests to run without including in results.
    size: Size of the flow, in bytes.
    iterations: Number of tests to do / results to attempt to return.
    use_rc3: If True, use RC3 instead of normal TCP. Handled inside fcttest.
    '''

    results = []

    h1, h2 = net.getNodeByName('h1', 'h2')

    rc3_arg_setting = "-r" if use_rc3 else ""

    # Start server
    p_srv = h2.popen('./fcttest -s -p 5678 -g %d %s' % (size, rc3_arg_setting),
                     stdout = subprocess.PIPE, stderr = subprocess.PIPE)

    # Run the client iterations + skip times
    for i in range(0,iterations + skip):
        p_clt = h1.popen('./fcttest -c -a %s -p 5678 -g %d %s'
                         % (h2.IP(), size, rc3_arg_setting),
                         stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (out, err) = p_clt.communicate()
        if err or p_clt.returncode != 0:
            print "[ERROR]: fcttest client error:", err
        else:
            skip_this = i < skip
            time = float(out)
            print "skip_this = %s, use_rc3 = %s, size = %d, time (ms) = %f" \
                   % (skip_this, str(use_rc3), size, time)
            if not skip_this:
               results.append(time)

    # Kill the server
    if p_srv.poll() is None:
      p_srv.kill()
    else:
      (out, err) = p_srv.communicate()
      print "[ERROR]: fcttest error: %s" % err

    return results

def setupNetVariables():
    '''Setup Linux networking variables.

    As prescribed by the RC3 linux patch readme, at:
    https://github.com/NetSys/rc3-linux'''

    settings = ['net.ipv4.tcp_dsack=0',
                'net.ipv4.tcp_fack=0',
                'net.ipv4.tcp_timestamps=0',
                'net.core.wmem_max=2048000000',
                "net.ipv4.tcp_wmem='10240 2048000000 2048000000'",
                'net.core.rmem_max=2048000000',
                "net.ipv4.tcp_rmem='10240 2048000000 2048000000'"];
    for setting in settings:
        subprocess.call("sysctl %s" % (setting,), shell=True)

def rc3Test(bandwidth, flowLen):

    setupNetVariables()

    topo = RC3Topo(bandwidth)
    net = Mininet(topo, link=TCLink)
    net.start()

    print "Dumping node connections"
    dumpNodeConnections(net.hosts)

    h1, h2 = net.getNodeByName('h1', 'h2')

    print "Configuring qdiscs"
    addPrioQdisc(h1, 'h1-eth0', bandwidth, DELAY)
    addPrioQdisc(h2, 'h2-eth0', bandwidth, DELAY)
    #TODO do we need this at the switch too?

    #print "Testing bandwidth between 'h1' and 'h2'"
    #h2.sendCmd('iperf -s')
    #result = h1.cmd('iperf -c', h2.IP(), '-n', flowLen)
    #print result

    '''
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
    '''

    # TODO global?
    # Link delay is scaled by 100, and rate by 1/100, so flow completion times
    # must be scaled by 1/100
    time_scale_factor = 1.0/100

    # TODO FIXME
    # scale_factor = 1.0/10

    # TODO These don't seem to help, at 100 or 10000

    #h1.cmdPrint("ifconfig h1-eth0 txqueuelen 100")
    #h1.cmdPrint("ifconfig lo txqueuelen 100")
    #h1.cmdPrint("ifconfig")
    #h2.cmdPrint("ifconfig h2-eth0 txqueuelen 100")
    #h2.cmdPrint("ifconfig lo txqueuelen 100")
    #h2.cmdPrint("ifconfig")

    #h1.cmdPrint("ifconfig h1-eth0 txqueuelen 100")
    #h1.cmdPrint("ifconfig lo txqueuelen 100")
    #h1.cmdPrint("ifconfig")
    #h2.cmdPrint("ifconfig h2-eth0 txqueuelen 100")
    #h2.cmdPrint("ifconfig lo txqueuelen 100")
    #h2.cmdPrint("ifconfig")

    #CLI(net)

    do_fct_tests(net, 3, time_scale_factor=time_scale_factor,
                 starter_data_function = figure15a_paper_data,
                 fig_file_name = 'figure15a.png')

    #CLI(net)

    net.stop()

if __name__ == '__main__':
    lg.setLogLevel('info')
    rc3Test(LINK_BW_1, 20000000)
