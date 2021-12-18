import DB
import ServerComs
import ServerProtocol
import queue
import RSAClass
import random
import string as string_c
from scapy.all import *
import AESClass
import StationComs
import OnionServer
import ProxyComs

# def wait_for_packet():
#     """
#
#     :return: waits for the a msg
#     """
#     while True:
#         if not http_q.empty():
#             packet = http_q.get()
#             # roll stations for the msg
#             stations_for_msg = roll_stations()
#             # get the ip of the last station
#             lastIP = stations_for_msg[-1]
#             # save the destination ip
#             dst_ip = packet[IP].dst
#             # save the ip of the client
#             client_IP = packet[IP].src
#             # roll port
#             chosen_port = roll_port()
#             # send the port to all the stations and wait for the accept
#             for station_ip in stations_for_msg:
#                 received_ok = False
#                 # send the port to the station
#                 while not received_ok:
#                     # build by protocol
#                     msg = ServerProtocol.buildSendPort(chosen_port)
#                     # encrypt
#                     msg = ip_key_dict[station_ip].encrypt(msg)
#                     # send the msg
#                     my_server.sendMsg(station_ip, msg)
#                     print("Sent port " + str(chosen_port))
#                     # wait for ok
#                     ip, data = q.get()
#                     msg = ip_key_dict[station_ip].decrypt(data)
#                     code, msg = ServerProtocol.unpack(msg)
#                     # received OK
#                     if code == "05":
#                         print("OK")
#                         received_ok = True
#
#             # change the ip in the packet
#             packet[IP].src = stations_for_msg[-1]
#             data_of_msg = packet[Raw].load
#             # after the stations servers are up save the data on the msg
#             port_dict[chosen_port] = (client_IP, dst_ip, stations_for_msg)
#             # open the code that sends the msg
#             threading.Thread(target=handle_send_receive_msg,args=(data_of_msg, chosen_port, client_IP, dst_ip, stations_for_msg)).start()


def handle_send_receive_msg(data, port, client_port, dst_ip, stations, ret_msg_queue):

    """

    :param data: the sniffed data
    :param port: port to receive and send on
    :param clientIP: the IP address of the client
    :param dst_ip: the destination IP (site IP)
    :param stations: list of the chosen stations for sending the msg
    sends the msg to the first station and receives response
    :return:
    """
    # creating listening server
    listening_q = queue.Queue()
    listenting_server = ServerComs.ServerComs(int(port), listening_q)

    sending_q = queue.Queue()
    # creating sending client
    sending_client = StationComs.StationComs(port, stations[0], sending_q)

    # creating the list of tuples containing the ip and the key
    ip_key_list = []
    for i in range(len(stations)):
        ip_key_list.append((stations[i], ip_key_dict[stations[i]]))
    # building layers on top of the packet

    msg = OnionServer.buildLayerAll(data, ip_key_list, dst_ip)
    # sends the msg forward
    sending_client.sendMsg(msg)

    # wait for the returning msg from the site
    ip, ret_msg = listening_q.get()
    send_msg_to_client(ret_msg, client_port, ip_key_list, ret_msg_queue)


def send_msg_to_client(ret_msg, client_port, ip_key_list, ret_msg_queue):
    """

    :param ret_msg: the returning msg from the site
    :param clientIP: the ip of the client
    :return: sends the data from the site to the client
    """
    # create the list of the decrypting keys
    list_of_keys = []
    for i in range(len(ip_key_list)-1, -1, -1):
        list_of_keys.append(ip_key_list[i][1])
    # remove all the layers
    ret_msg = OnionServer.removeLayerAll(ret_msg, list_of_keys)
    print("SENDING BACK TO USER - " + str(ret_msg))
    ret_msg_queue.put((client_port, ret_msg))


def proxy():
    """

    :return: opens the proxy server and puts the data received in the q as (ip, dstip, dstport, msg)
    """
    # set up proxy server
    proxy_queue = queue.Queue()
    proxy_server = ProxyComs.ProxyComs(8080, proxy_queue)
    # returning msgs to send back to client
    ret_msg_queue = queue.Queue()
    # handle msg's from the proxy server
    while True:
        # extract a msg
        client_port, msg = proxy_queue.get()
        print("MSG- ", msg)
        # if its a GET request
        if msg.startswith("GET"):
            print("MSG- ", msg)
            # extract the url
            url = msg.split("/")[2]
            print("URL", url)
            # get the ip of the url
            dst_ip = socket.gethostbyname(url)

            # roll stations for the msg
            stations_for_msg = roll_stations()
            # get the last station
            lastIP = stations_for_msg[-1]

            # roll port
            port = roll_port()

            # send the port to all the stations and wait for the accept
            for station_ip in stations_for_msg:

                received_ok = False
                # send the port to the station
                while not received_ok:
                    # build by protocol
                    chosen_port = ServerProtocol.buildSendPort(port)
                    print("Sent port " + str(chosen_port))
                    # encrypt
                    chosen_port = ip_key_dict[station_ip].encrypt(chosen_port)
                    # send the port
                    my_server.sendMsg(station_ip, chosen_port)
                    # wait for ok
                    ip, data = q.get()
                    ok_msg = ip_key_dict[station_ip].decrypt(data)
                    code, ok_msg = ServerProtocol.unpack(ok_msg)
                    # received OK
                    if code == "05":
                        print("OK")
                        received_ok = True
            # after the stations servers are up save the data on the msg
            port_dict[chosen_port] = (client_port, dst_ip, stations_for_msg)
            # open the code that sends the msg
            threading.Thread(target=handle_send_receive_msg, args=(msg, port, client_port, dst_ip, stations_for_msg, ret_msg_queue)).start()
        # if there is a msg to send back
        elif not ret_msg_queue.empty():
            # get  the ip and the msg to return
            (clientIP, msg) = ret_msg_queue.get()
            print()
            print()
            print()
            print("CLIENT PORT - ", client_port, "MSG- ", msg)
            # return the msg to the client
            proxy_server.sendMsg(client_port, msg)
            # disconnect the client
            proxy_server.disconnect(client_port)


def roll_port():
    """

    :return: unused port
    """
    found = False
    while not found:
        port = random.randint(2000,50000)
        # check if port not in use
        if not port in port_dict.keys():
            found = True
    return port


def roll_key():
    """

    :return: randomizing a String for symetric key with length of 16 and returns it
    """

    l = string_c.ascii_letters + "123456789"
    string = ''
    for i in range(16):
        char = random.choice(l)
        string += char

    if string in ip_key_dict.values():
        return roll_key()
    else:
        return string


def roll_stations():
    """

    :return: chooses 3 stations from the list and returns a list containing their ip
    """

    stations_for_the_msg = []
    count = station_per_msg
    while count > 0:
        # get a station ip from the dictionary
        ip_adr = random.choice(list(ip_key_dict.keys()))
        if ip_adr not in stations_for_the_msg:
            count = count - 1
            stations_for_the_msg.append(ip_adr)

    return stations_for_the_msg


q = queue.Queue()
my_server = ServerComs.ServerComs(59185, q)
ip_key_dict = {} # ip : key
ip_mac_dict = {}
rsa_keys = RSAClass.RSAClass()
public_key = rsa_keys.get_public_key_pem().decode()
station_per_msg = 1
ToriDB = DB.DB("ToriDB")
http_q = queue.Queue()
port_dict = {}  # port : (ip of client, ip of the site , list of stations for the msg)
port_dict[59185] = None
ToriDB.addStation("64:00:6a:42:4a:de")

while True:
    # server for connection and change in keys
    ip, data = q.get()
    # if the ip hasn't connected yet
    if not ip in list(ip_key_dict.keys()):
        code, msg = ServerProtocol.unpack(data)

        # msg is the mac address
        if code == "00":
            mac_adr = msg
            # check if the station exists in the white list
            if ToriDB.checkStation(mac_adr):
                ip_mac_dict[ip] = mac_adr
                msg_ret = ServerProtocol.buildPublishPKeySE(public_key)
                my_server.sendMsg(ip, msg_ret)

            else:
                my_server.disconnect(ip)
        # check if the communication is permitted
        if ip in ip_mac_dict:
            # station sent pkey
            if code == "02":
                station_pkey = msg.encode()
                sym_key = roll_key()
                msg_ret = ServerProtocol.buildSendSymetricKey(sym_key)
                # encrypt the symteric key with the station's public key
                encrypted = RSAClass.encrypt_msg(msg_ret, station_pkey)
                # send the symetric key
                my_server.sendMsg(ip, encrypted)
                # add the key to the dictionary
                ip_key_dict[ip] = AESClass.AESCipher(sym_key)
                if len(ip_key_dict) >= station_per_msg:
                    threading.Thread(target=proxy).start()
        else:
            # if the communication is not permitted , kick the ip off the server
            my_server.disconnect(ip)
    else:
         # put back in the queue
         q.put((ip, data))





