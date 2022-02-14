import StationProtocol
import queue
import RSAClass
import StationComs
import AESClass
import uuid
import threading
import ServerComs
import OnionStation
from scapy.all import *
import socket
import select


def send_and_receive_site(site_IP, msg):
    """

    :param site_IP: the IP of the site
    :param msg: The msg to the to the site
    :return: returns the data from the response packet of the server
    """
    # create the socket connection to the site
    socket_to_site = socket.socket()
    try:
        socket_to_site.connect((site_IP, 80))
        socket_to_site.send(msg.encode())
    except:
        msg = bytearray()
    else:
        while True:
            rlist, wlist, xlist = select.select([socket_to_site],[],[])
            if rlist:
                try:
                    data = socket_to_site.recv(1024)
                except:
                    msg = bytearray()
                    break
                if data == b'':
                    break
                msg.extend(data)
            else:
                break

    return msg


def send_and_Connect_site(site_IP):
    socket_to_site = socket.socket()
    try:
        socket_to_site.connect((site_IP, 443))
    except:
        return 'False'
    else:
        browsers[site_IP] = (socket_to_site)
        return 'True'


def open_listening_server(port):
    """

    :param port: the port to listen on
    :return: opens a listening server on the port receives and sends the data forward
    """
    # listen for the msg
    listening_q = queue.Queue()
    listening_server = ServerComs.ServerComs(port, listening_q)

    # build an OK response
    OK_msg = StationProtocol.buildOKMsg()
    # encrypt the msg
    OK_msg_enc = sym_key.encrypt(OK_msg)
    # send to the server that the station's listening server is up
    client.sendMsg(OK_msg_enc)

    print("sent OK")

    # receive the msg from another station/the server
    previous_station, msg = listening_q.get()
    # remove one layer
    data = OnionStation.remove_layer(msg, sym_key)
    print("received data- " + str(data))

    # extract the info
    code = data[0]
    next_station = data[1][0]
    site_IP = data[1][1]
    msg = data[1][2]
    if code == '06':
        site_port = 80
    elif code == '17':
        site_port = 443
    previous_port = port
    # if the next station is the site, needs to send on port 80
    print("NEXT STATION - " + str(next_station), "SITE_IP - " + str(site_IP))
    # in case the next station is the site
    if next_station == site_IP:
        if code == '06':
            data = send_and_receive_site(site_IP, msg)
        elif code == '17':
            data = send_and_Connect_site(site_IP)

        if msg == bytearray():
            listening_server.close_server()

    # next station is a normal station
    else:
        # create sending client
        sending_q = queue.Queue()
        sending_client = StationComs.StationComs(port, next_station, sending_q)
        # send the msg to the site/next station
        sending_client.sendMsg(msg)

        # wait for returning msg
        site_IP, data = listening_q.get()
        print("data from another station - " + str(data))

    # build a layer on top of the returning msg
    print("BEFORE ENC", data)
    if site_port == 80:
        ret_msg = OnionStation.buildLayer(data, sym_key)
    elif site_port == 443:
        ret_msg = OnionStation.buildLayerConnect(site_IP, 443, sym_key)
    print("ENC", ret_msg)

    # send the msg to the previous station
    sending_q = queue.Queue()
    sending_client = StationComs.StationComs(previous_port, previous_station, sending_q)
    # send the msg to the previous station
    sending_client.sendMsg(ret_msg)


# get the mac address of the station
mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                for ele in range(0, 8 * 6, 8)][::-1])
first_con_q = queue.Queue()
# create a station client
client = StationComs.StationComs(59185, "192.168.4.97", first_con_q)
# send mac address
print("mymac", mac)
msg = StationProtocol.buildSendMacAdr(mac)
print("msg", msg)
client.sendMsg(msg)
# create public and private keys
rsa_keys = RSAClass.RSAClass()
# list of all the browsers sockets
browsers = {}   # siteIP:siteSocket
# get the public key
public_key = rsa_keys.get_public_key_pem().decode()

connecting = True
while connecting:
    data = first_con_q.get().decode()
    code, msg = StationProtocol.unpack(data)

    # server sending public key
    if code == "01":
        server_pkey = msg
        print(server_pkey)
        msg_ret = StationProtocol.buildPublishKeyST(public_key)
        # send the public
        client.sendMsg(msg_ret)
        # wait for the symetric key msg
        data = first_con_q.get()
        print("DATA = " + str(data))
        # decrypt the msg
        msg = rsa_keys.decrypt_msg(data).decode()
        print("MSG = " + str(msg))
        code, sym_key = StationProtocol.unpack(msg)
        print("SYMKEY = " + sym_key)
        # build AESCipher with the symetric key
        sym_key = AESClass.AESCipher(sym_key)
        connecting = False

# after the station finished connecting
while True:
    data = first_con_q.get()
    data = sym_key.decrypt(data)
    code, msg = StationProtocol.unpack(data)
    print("data = " + str(data), "code = " + str(code))
    # the server has sent port
    if code == "04":
        port = msg
        threading.Thread(target=open_listening_server, args=(int(port),)).start()
