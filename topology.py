"""Two OpenFlow13 switches, four hosts, remote Ryu controller."""
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink


def main():
    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    s1 = net.addSwitch('s1', dpid='0000000000000001', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', dpid='0000000000000002', protocols='OpenFlow13')
    hosts = [net.addHost('h%d' % i, ip='10.0.0.%d/24' % i) for i in range(1, 5)]
    net.addLink(hosts[0], s1)
    net.addLink(hosts[1], s1)
    net.addLink(hosts[2], s2)
    net.addLink(hosts[3], s2)
    net.addLink(s1, s2)
    try:
        net.start()
        info('\nHost addresses: h1=10.0.0.1 h2=10.0.0.2 h3=10.0.0.3 h4=10.0.0.4\n')
        info('Test: pingall | h3 python3 -m http.server 8000 & | h1 curl http://10.0.0.3:8000\n')
        CLI(net)
    finally:
        net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
