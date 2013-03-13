#!/usr/bin/python

"CS244 Spring 2013 Assignment 3: MoshTest"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE, call
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

import termcolor as T

import sys
import os
import math
import datetime
from os import listdir

# Number of samples to take in get_rates() before returning.
NSAMPLES = 3

# Time to wait between samples, in seconds, as a float.
SAMPLE_PERIOD_SEC = 1.0
#SAMPLE_PERIOD_SEC = 0.5

# Time to wait for first sample, in seconds, as a float.
SAMPLE_WAIT_SEC = 3.0
CALIBRATION_SAMPLES = 20
CALIBRATION_SKIP = 10
#from pprint import pprint

def cprint(s, color, cr=True):
    """Print in color
       s: string to print
       color: color to use"""
    if cr:
        print T.colored(s, color)
    else:
        print T.colored(s, color),


parser = ArgumentParser(description="Mosh tests")

class MoshTopo(Topo):

    def __init__(self, n=2):
       super(MoshTopo, self).__init__()

        # TODO: create two hosts
       h1 = self.addHost('h1')
       h2 = self.addHost('h2')
       h3 = self.addHost('h3')
       h4 = self.addHost('h4')
       h5 = self.addHost('h5')
       h6 = self.addHost('h6')
       h7 = self.addHost('h7')
       h8 = self.addHost('h8')

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
       s0 =self.addSwitch('s0')
       s1 =self.addSwitch('s1')
       s2 =self.addSwitch('s2')
       s3 =self.addSwitch('s3')

       self.addLink(h1, s0, bw=25, delay="30ms", max_queue_size=40, use_htb=True, loss=8)
       self.addLink(h2, s0, bw=1, delay="450ms", max_queue_size=40, use_htb=True, loss=1)
       self.addLink(h3, s1, bw=25, delay="30ms", max_queue_size=40, use_htb=True, loss=8)
       self.addLink(h4, s1, bw=1, delay="450ms", max_queue_size=40, use_htb=True, loss=1)
       self.addLink(h5, s2, bw=25, delay="30ms", max_queue_size=40, use_htb=True, loss=8)
       self.addLink(h6, s2, bw=1, delay="450ms", max_queue_size=40, use_htb=True, loss=1)
       self.addLink(h7, s3, bw=25, delay="30ms", max_queue_size=40, use_htb=True, loss=8)
       self.addLink(h8, s3, bw=1, delay="450ms", max_queue_size=40, use_htb=True, loss=1)
       # TODO: Add links with appropriate characteristics
       return

def get_hosts(net):
    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')
    h3 = net.getNodeByName('h3')
    h4 = net.getNodeByName('h4')
    h5 = net.getNodeByName('h5')
    h6 = net.getNodeByName('h6')
    h7 = net.getNodeByName('h7')
    h8 = net.getNodeByName('h8')
    return h1, h2, h3, h4, h5, h6, h7, h8

def verify_latency(net):

    #use time() to get an estimate of the RTT. So far its always close to the actual RTT returned by ping
    h1, h2, h3, h4 = get_hosts(net)
    count = 1
    start = time()
    h1.cmdPrint('ping %s -c %d' %(h2.IP(), count))
    end = time()
    
    print "Latency from h1 to h2 is %f" %(end-start)

    start = time()
    h4.cmdPrint('ping %s -c %d' %(h4.IP(), count))
    end = time()

    print "Latency from h3 to h4 is %f" %(end-start)

def get_txbytes(iface):
    f = open('/proc/net/dev', 'r')
    lines = f.readlines()
    for line in lines:
        if iface in line:
            break
    f.close()
    if not line:
        raise Exception("could not find iface %s in /proc/net/dev:%s" %
                        (iface, lines))

def get_rates(iface, nsamples=NSAMPLES, period=SAMPLE_PERIOD_SEC,
              wait=SAMPLE_WAIT_SEC):
    """Returns the interface @iface's current utilization in Mb/s.  It
    returns @nsamples samples, and each sample is the average
    utilization measured over @period time.  Before measuring it waits
    for @wait seconds to 'warm up'."""
    # Returning nsamples requires one extra to start the timer.
    nsamples += 1
    last_time = 0
    last_txbytes = 0
    ret = []
    sleep(wait)
    while nsamples:
        nsamples -= 1
        txbytes = get_txbytes(iface)
        now = time()
        elapsed = now - last_time
        #if last_time:
        #    print "elapsed: %0.4f" % (now - last_time)
        last_time = now
        # Get rate in Mbps; correct for elapsed time.
        rate = (txbytes - last_txbytes) * 8.0 / 1e6 / elapsed
        if last_txbytes != 0:
            # Wait for 1 second sample
            ret.append(rate)
        last_txbytes = txbytes
        print '.',
        sys.stdout.flush()
        sleep(period)
    return ret

#values returned: { median, max, stdev }
def get_rate_details(iface):
    rates = get_rates(iface, nsamples=CALIBRATION_SAMPLES+CALIBRATION_SKIP)
    print "measured calibration rates: %s" % rates
    # Ignore first N; need to ramp up to full speed.
    rates = rates[CALIBRATION_SKIP:]
    return median(rates), max(rates), stdev(rates)

def start_receiver(net, receiver):
    server = receiver.popen("iperf -s", shell=True)

def start_sender(sender, recipient, seconds):
    sender.popen("iperf -c %s -t %d"
             %(recipient.IP(), seconds))

def verify_bandwidth(net, iface):
    print "VERIFYING BANDWIDTH......"
    seconds = 100
    h1, h2, h3, h4 = get_hosts(net)
    #start some iperfs
    start_receiver(net, h2)
    start_sender(h1, h2, seconds)
    rate_median, rate_max, rate_stdev = get_rate_details(iface)
    rate_fraction = rate_median/args.bw_net
    cprint ("Verify bandwidth for %s: Reference rate median: %.3f max: %.3f stdev: %.3f fraction: %.3f" %
            (iface, rate_median, rate_max, rate_stdev, rate_fraction), 'blue')

    sys.stdout.flush()
    os.system('killall -9 iperf')
    sleep(5)

def log_time(filename):
    f = open("./%s"%filename, 'w')
    now = datetime.datetime.now()
    f.write(now.strftime("%Y-%m-%d-%H:%M:%S"))
    f.close()

def plot_results(sortedFile, sortedDir):
    cmd = "sudo python ~/CS244-Mosh/plot.py ~/CS244-Mosh/%s/%s" %(sortedDir,sortedFile)
    print cmd
    call(cmd, shell=True)

#reads in a result file, sorts it, and write out values with corresponding percentages
def generate_plottable_result(resultFile,resultDir,sortedFile, sortedDir):
    f = open("./%s/%s" %(resultDir,resultFile))
    content = f.readlines()
    f.close()
    values = [float(val) for val in content]
    values.sort()
    length = len(values)
    f = open("./%s/%s" %(sortedDir,sortedFile), 'w')
    f.truncate()
    count = 1
    for val in values:
        percentage = count/float(length)
        count += 1
        f.write("%s,%s\n" %(val,percentage))
    f.close()    
        
def run_replay(host, cmd, retVals, resultFiles, session, connType):
    print "running %s\n" %cmd
    #p1 = host.popen("%s > %s" %(cmd,"tt2"), shell=True)
    pRes = host.popen("%s" %(cmd), shell=True)
    retVals.append(pRes)
    resultFiles.append("%s-%s.out"%(connType,session))
    print "running %s\n" %cmd

def mosh_test():
    topo = MoshTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    #net.pingAll()


    #verify_latency(net)
    #s0-eth1: s0-h1 (wifi)
    #s0-eth2: s0-h2 (3g)
    #s1-eth1: s1-h3 (wifi)
    #s1-eth2: s1-h4 (3g)

    #verify_bandwidth(net, iface='s0-eth1')

    log_time("start.log")
    logDir = "logs"
    logs = listdir("./%s"%logDir)

    now = datetime.datetime.now()

    resultsDir = "results-" + now.strftime("%Y-%m-%d-%H:%M:%S")

    if not os.path.exists(resultsDir):
        os.makedirs(resultsDir)


    h1,h2,h3,h4,h5,h6,h7,h8 = get_hosts(net)

    pbkey = "./CS244EC2.pem"
    sshd = "/usr/sbin/sshd"
    opts = "-D"
    openvpn_c_cmd = "/usr/sbin/openvpn --config openvpn_client.conf"
    openvpn_s_cmd = "/usr/sbin/openvpn --config openvpn_server.conf"

    print "Start sshd on h2 h4 h6 h8\n"
    h2.cmd(sshd + ' ' + opts + '&' )
    h4.cmd(sshd + ' ' + opts + '&' )
    h6.cmd(sshd + ' ' + opts + '&' )
    h8.cmd(sshd + ' ' + opts + '&' )

    print "Start openvpn on h6 and h8\n"
    h6.cmd(openvpn_s_cmd + '&')
    h8.cmd(openvpn_s_cmd + '&')

    print "starting openvpn clients"
    h5.cmd(openvpn_c_cmd + ' --remote %s 1194 &' % (h6.IP()))
    h7.cmd(openvpn_c_cmd + ' --remote %s 1194 &' % (h8.IP()))

    openvpn_tunnel_IP = "10.11.12.1"
    
    popenRetVals = []
    popenResFiles = []
    for log in logs:    
        session = log.replace(".log","")
        #prepare replay cmds
        replaySshCmds = "./term-replay-client-orig ./%s/%s ./%s/ssh-%s.out ssh ubuntu@%s -i ./CS244EC2.pem -o \\'StrictHostKeyChecking no\\' \"./term-replay-server ./%s/%s\"" %(logDir,log,resultsDir,session,h2.IP(),logDir,log)
        moshInnerSSH = "ssh -o \\'StrictHostKeyChecking no\\' -i ./CS244EC2.pem"
        replayMoshCmds = './term-replay-client-orig ./%s/%s ./%s/mosh-%s.out mosh ubuntu@%s --ssh=\\"%s\\" -- ~/CS244-Mosh/term-replay-server ~/CS244-Mosh/%s/%s' %(logDir,log,resultsDir,session,h4.IP(),moshInnerSSH,logDir,log)

        #replay with vpn
        replaySshVpnCmds = "./term-replay-client-orig ./%s/%s ./%s/ssh-vpn-%s.out ssh ubuntu@%s -i ./CS244EC2.pem -o \\'StrictHostKeyChecking no\\' \"./term-replay-server ./%s/%s\"" %(logDir,log,resultsDir,session,openvpn_tunnel_IP,logDir,log)
        replayMoshVpnCmds = './term-replay-client-orig ./%s/%s ./%s/mosh-vpn-%s.out mosh ubuntu@%s --ssh=\\"%s\\" -- ~/CS244-Mosh/term-replay-server ~/CS244-Mosh/%s/%s' %(logDir,log,resultsDir,session,openvpn_tunnel_IP,moshInnerSSH,logDir,log)

        run_replay(h1, replaySshCmds, popenRetVals, popenResFiles, session, "ssh")
        run_replay(h3, replayMoshCmds, popenRetVals, popenResFiles, session, "mosh")
        run_replay(h5, replaySshVpnCmds, popenRetVals, popenResFiles, session, "ssh-vpn")
        run_replay(h7, replayMoshVpnCmds, popenRetVals, popenResFiles, session, "mosh-vpn")


    #create directory for sorted output
    sortedDir = resultsDir.replace("results","sorted")
    if not os.path.exists(sortedDir):
        os.makedirs(sortedDir)

    print "made dir %s\n" %sortedDir
        
    count = 0
    popenDone = []
    while(True):
        sleep(10)
        for idx, popenRetVal in enumerate(popenRetVals):
            pollVal = popenRetVal.poll()
            if(pollVal is None):
                print "Still running: %s\n"%popenResFiles[idx]
            else:
                if idx not in popenDone:
                    rf = popenResFiles[idx]
                    print "Done: %s\n"%rf
                    popenDone.append(idx)
                    sf = "%s.sorted" %rf
                    generate_plottable_result(rf, resultsDir, sf, sortedDir)
                    plot_results(sf, sortedDir)
        if(len(popenDone) == len(popenResFils):
               break;
        print "-------------\n"                
        count += 1
        count = count % 6
        if(count == 0):
            #print out all done every min
            if len(popenDone) == 0:
                print "---None done yet---\n"
            else:
                print "---Done Summary---\n"
                for done in popenDone:
                    print "%s\n"%popenResFiles[done]

    log_time("end.log")
    print "The end"

    print "Please find these plots in the following directory: %s" %sortedDir
    for rf in popenResFiles:
        print "%s\n"%rf

    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()
    #h1.cmd( 'kill %' + sshd )
    #h2.cmd( 'kill %' + sshd )


if __name__ == "__main__":
    mosh_test()
