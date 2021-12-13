from scapy.all import *
import socket
import queue



def my_filter(packet):
    return TCP in packet and packet.dport == 80


def handle_pack(packet):
    http_q.put(packet)


def scapy_sniff():
    sniff(lfilter=my_filter, prn=handle_pack)

threading.Thread(target=scapy_sniff).start()


while True:
    packet = http_q.get()
    print(packet.show())
    packet[IP].src = '1.1.1.1'
    print(packet.show())



