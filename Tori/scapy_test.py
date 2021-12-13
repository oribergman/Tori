from scapy.all import *

packet = IP(dst= '1.1.1.1')/TCP(dport=80)/Raw(load="GET MY ASS")
packet.show()

