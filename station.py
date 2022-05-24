import sys
import StationProtocol
import queue
import RSAClass
import StationComs
import AESClass
import uuid
import threading
import ServerComs
import OnionStation
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
        msg = bytearray()
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
                if len(data) < 1024:
                    break
            else:
                break

    return msg


def receive_HTTPS(socket_to_site, previous_com, sym_key):
    """

    :param socket_to_site: the socket that is connected to the site
    :param previous_com: the serverCom of the previous station
    :param sym_key: the symetric key (AESCipher)
    :return: receives from the site and sends to the previous station
    """
    receiving = True

    while receiving:
        msg = bytearray()
        while True:

            rlist, wlist, xlist = select.select([socket_to_site], [], [])

            if rlist:
                try:
                    data = socket_to_site.recv(1024)
                except:
                    msg = bytearray()
                    receiving = False
                    break
                else:
                    msg.extend(data)
                    if len(data) < 1024:
                        break

        if msg != bytearray(b''):
            msg = OnionStation.buildLayerHTTPS(msg, sym_key)
            previous_com.sendMsg(msg)


def send_HTTPS(listening_q, sym_key, socket_to_site):
    """

    :param listening_q: queue of data from previous station
    :param sym_key: symetric key for encryption
    :param previous_com: StationComs object connected to last station
    :return: sends to the server all the data from the previous station
    """
    while True:
        previous_ip, data = listening_q.get()
        if data == "dc":
            sys.exit()
        data = sym_key.decrypt(data)
        code, msg = StationProtocol.unpack(data)
        socket_to_site.send(bytearray(msg))


def send_and_Connect_site(site_IP, listening_q, previous_station, previous_port, sym_key):
    """

    :param site_IP: the ip of the site
    :param listening_q: the listening queue from the server/previous station
    :param previous_station: the serverCom of the server/previous station
    :param previous_port: the previous port the msg has been sent on
    :param sym_key: the symetric key (AESCipher)
    :return: connects to the site and opens the thread to receive and send from site and to send from server to site
    """
    socket_to_site = socket.socket()
    try:
        socket_to_site.connect((site_IP, 443))
    except:
        print("No connection to ", site_IP, "Could be made")
        return 'False'
    else:
        browsers[site_IP] = (socket_to_site)
        temp_q = queue.Queue()
        previous_com = StationComs.StationComs(previous_port, previous_station, temp_q)
        # receiving thread from server (sends to previous station)
        threading.Thread(target=receive_HTTPS, args=(socket_to_site, previous_com, sym_key, )).start()
        # receiving thread from stations (sends to server)
        threading.Thread(target=send_HTTPS, args=(listening_q, sym_key, socket_to_site, )).start()
        return 'True'


def receive_station_HTTPS(listening_q, next_com, previous_com, sym_key, previousIP, nextIP):
    """
    :param listening_q: the queue of the coms from previous station
    :param next_com: the StationCom object of the next station in line
    :param sym_key: the symetric key of the station
    :param previous_com: the StationCom object of the previous station in line
    :return: receives from the previous station and forwards (HTTPS) (from server to browser) or (from browser to server)
    """
    while True:
        IP, data = listening_q.get()
        if data != b"dc":
            # if the msg is from the previous station so forward the msg towards the browser
            if IP == previousIP:
                # remove one layer from the msg
                data = sym_key.decrypt(data)
                code, msg = StationProtocol.unpack(data)
                # forward to next station
                next_com.sendMsg(msg)

            # if the msg is from the next station so forward the msg to the previous station
            elif IP == nextIP:
                # add layer to the msg
                new_msg = OnionStation.buildLayerHTTPS(data, sym_key)
                # forward to previous station
                previous_com.sendMsg(new_msg)
        else:
            sys.exit()


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
    print("encrypted OK", OK_msg_enc, "OK", OK_msg)
    # send to the server that the station's listening server is up
    client.sendMsg(OK_msg_enc)

    # receive the msg from another station/the server
    previous_station, msg = listening_q.get()
    if msg == b"dc":
        sys.exit()
    msg = msg.decode()

    # remove one layer
    data = OnionStation.remove_layer(msg, sym_key)

    # print("received data- " + str(data), "FROM", previous_station)

    code = data[0]

    if code == "17":
        # extract the info
        next_station = data[1][0]
        site_IP = data[1][1]
        site_port = data[1][2]
        msg = data[1][3]

    elif code == "06":
        # extract the info
        next_station = data[1][0]
        site_IP = data[1][1]
        msg = data[1][2]

    previous_port = port

    # create the stationCom object to forward msg
    sending_q = queue.Queue()
    sending_client_previous = StationComs.StationComs(previous_port, previous_station, sending_q)

    # in case the next station is the site
    if next_station == site_IP:
        if code == '06':
            data = send_and_receive_site(site_IP, msg)
        elif code == '17':
            connected = send_and_Connect_site(site_IP, listening_q, previous_station, previous_port, sym_key)

        if msg == bytearray():
            listening_server.close_server()

    # next station is a normal station
    else:
        # create sending client
        sending_q = queue.Queue()
        sending_client_forward = StationComs.StationComs(port, next_station, sending_q)
        # send the msg to the site/next station
        sending_client_forward.sendMsg(msg)

        # wait for returning msg
        next_station, data = listening_q.get()
        if data == b"dc":
            sys.exit()
        data = data.decode()

        # connection established
        if code == "17":
            threading.Thread(target=receive_station_HTTPS, args=(
            listening_q, sending_client_forward, sending_client_previous, sym_key, previous_station,
            next_station)).start()
        if data == b"dc":
            sys.exit()
        connected = "True"

    if code == "06":
        ret_msg = OnionStation.buildLayer(data, sym_key)
    elif code == "17" and connected == "True":
        ret_msg = OnionStation.buildLayerConnect(site_IP, 443, sym_key, data)
    else:
        sys.exit()
    # send the msg to the previous station
    sending_client_previous.sendMsg(ret_msg)


# get the mac address of the station
mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                for ele in range(0, 8 * 6, 8)][::-1])
first_con_q = queue.Queue()
# create a station client
client = StationComs.StationComs(59185, "192.168.4.73", first_con_q)
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

port_list = []
# after the station finished connecting
while True:
    data = first_con_q.get()
    data = sym_key.decrypt(data).decode()
    code, msg = StationProtocol.unpack(data)

    # the server has sent port
    if code == "04":
        port = msg
        if port in port_list:
            print("Again", port)
        else:
            port_list.append(port)
            threading.Thread(target=open_listening_server, args=(int(port), )).start()
