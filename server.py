import socket
import sys
import threading

import DB
import ServerComs
import ServerProtocol
import queue
import RSAClass
import random
import string as string_c
import AESClass
import StationComs
import OnionServer
import ProxyComs


def wait_for_ok(stations_for_msg, sendingPort, station_server, station_server_q, ip_key_dict, port_list, client_address,dst_ip, ret_msg_queue, msg, codeMsg, port_stations, browserPort):
    """

    :param station_for_msg: all the stations for the specific msg
    :param port: the chosen port
    :param station_server: ServerComs of the stations
    :param station_server_q: queue of station_server
    :param ip_key_dict: dictionary of ip:symetric_key
    :param port_list: list of used ports
    :param client_address: (ip,port) of the client
    :param dst_ip: the ip of the browser
    :param msg: the msg to deliver
    :return: Sends the request of approval to the stations and waits for them to return OK
    """

    # send the port to all the stations and wait for the accept
    for station_ip in stations_for_msg:

        received_ok = False
        # send the port to the station
        while not received_ok:
            # build by protocol
            chosen_port = ServerProtocol.buildSendPort(sendingPort)
            # encrypt
            chosen_port = ip_key_dict[station_ip].encrypt(chosen_port)
            # send the port
            station_server.sendMsg(station_ip, chosen_port)
            # wait for ok
            ip, data = station_server_q.get()
            if data == b"dc":
                port_list.remove(sendingPort)
                del ip_key_dict[ip]
                sys.exit()
            else:
                if station_ip == ip :
                    if station_ip in ip_key_dict.keys():
                        data = data.decode()

                        try:
                            ok_msg = ip_key_dict[station_ip].decrypt(data)
                        except:
                            print("EXCEPTION DATA", data)

                        code, ok_msg = ServerProtocol.unpack(ok_msg)
                        # received OK
                        if code == "05":
                            received_ok = True
                            #print("GOT OK FROM", ip)
                    else:
                        station_server_q.put((ip, data))
                        sys.exit()

                else:
                    station_server_q.put((ip,data))

    # open the code that sends the msg
    handle_send_receive_msg(msg, sendingPort, client_address, dst_ip, browserPort, stations_for_msg, ret_msg_queue, codeMsg, port_stations)


def handle_send_receive_msg(data, port, client_address, dst_ip, browserPort, stations, ret_msg_queue, code, port_stations):

    """

    :param data: the sniffed data
    :param port: port to receive and send on
    :param client_address: the IP address of the client
    :param dst_ip: the destination IP (site IP)
    :param stations: list of the chosen stations for sending the msg
    sends the msg to the first station and receives response
    """
    # creating listening server
    listening_q = queue.Queue()
    listenting_server = ServerComs.ServerComs(int(port), listening_q)



    # creating sending client
    sending_q = queue.Queue()
    sending_client = StationComs.StationComs(port, stations[0], sending_q)



    # creating the list of tuples containing the ip and the key
    ip_key_list = []
    for i in range(len(stations)):
        ip_key_list.append((stations[i], ip_key_dict[stations[i]]))

    if code == '17':
        # building layers on the msg
        msg = OnionServer.buildLayerAllConnect(data, ip_key_list, dst_ip, browserPort)
        port_stations[port] = (stations, sending_client, client_address)

    elif code == '06':
        # building layers on top of the packet
        msg = OnionServer.buildLayerAll(data, ip_key_list, dst_ip)

    # sends the msg forward
    sending_client.sendMsg(msg)

    # wait for the returning msg from the site
    ip, ret_msg = listening_q.get()
    ret_msg = ret_msg.decode()

    # remove the port from the used ports
    port_list.remove(port)

    # send msg back to client
    send_msg_to_client(ret_msg, client_address, ip_key_list, ret_msg_queue, port,code)

    if code == "17":
        while True:
            # wait for the returning msg from the site
            ip, ret_msg = listening_q.get()

            # send the msg to the client
            send_msg_to_client(ret_msg, client_address, ip_key_list, ret_msg_queue, port)
            if ret_msg == b"dc":
                del port_stations[port]
                break

    else:
        # close the temporally server
        listenting_server.close_server()


def send_msg_to_client(ret_msg, client_address, ip_key_list, ret_msg_queue, port, code = 0):
    """

    :param ret_msg: the returning msg from the site
    :param clientIP: the ip of the client
    :return: sends the data from the site to the client
    """
    if code == "06":
        print("DECRYPTING 06", ret_msg)
    # create the list of the decrypting keys
    list_of_keys = []
    for i in range(len(ip_key_list)-1, -1, -1):
        list_of_keys.append(ip_key_list[i][1])

    # remove all the layers
    code, ret_msg = OnionServer.removeLayerAll(ret_msg, list_of_keys)
    ret_msg_queue.put((client_address, ret_msg, code, port))


def proxy(ip_key_dict, station_server, station_server_q, port_list, client_browser, port_stations):
    """

    :return: opens the proxy server rolls stations and rolls port and calls wait_for_ok
    """
    # set up proxy server
    proxy_queue = queue.Queue()
    proxy_server = ProxyComs.ProxyComs(8080, proxy_queue)
    # returning msgs to send back to client
    ret_msg_queue = queue.Queue()
    # handle msg's from the proxy server
    while True:
        while len(ip_key_dict) >= station_per_msg:
            if not proxy_queue.empty():
                # extract a msg
                client_address, msg = proxy_queue.get()
                if client_address not in client_browser.keys():
                    try:
                        msg = msg.decode()
                    except:
                        print(msg)
                        continue
                        
                    # if its a normal http request
                    if msg.startswith("GET") or msg.startswith("POST") or msg.startswith("HEAD") or msg.startswith("PUT") or msg.startswith("DELETE") or msg.startswith("OPTIONS"):
                        print("HTTP",msg)
                        # extract the url
                        url = msg.split("/")[2]
                        # get the ip of the url
                        try:
                            dst_ip = socket.gethostbyname(url)
                        except Exception as e:
                            print("Coundln't find link", url)
                            # invalid link
                            proxy_server.disconnect(client_address)

                        else:
                            # roll stations for the msg
                            stations_for_msg = roll_stations()
                            print("HTTP STATIONS", stations_for_msg)
                            # roll port
                            port = roll_port()
                            code = "06"
                            # wait for ok
                            threading.Thread(target=wait_for_ok, args=(stations_for_msg, port, station_server, station_server_q, ip_key_dict, port_list, client_address, dst_ip, ret_msg_queue, msg, code, port_stations, "80")).start()

                    # client want to open tunnel
                    elif msg.startswith('CONNECT'):
                        msgSplit = msg.split()
                        address = msgSplit[1]
                        if address.split(':')[1].isnumeric():
                            browserLink, browserPort = address.split(':')
                            try:
                                browserIP = socket.gethostbyname(browserLink)
                            except:
                                print("cant find", browserLink)
                                # invalid link
                                proxy_server.disconnect(client_address)
                            else:
                                # rolling port
                                sendingPort = roll_port()
                                # roll stations for the msg
                                stations_for_msg = roll_stations()

                                code = "17"
                                # deliver the msg
                                threading.Thread(target=wait_for_ok, args=(stations_for_msg, sendingPort, station_server, station_server_q, ip_key_dict, port_list, client_address, browserIP, ret_msg_queue, msg, code, port_stations, browserPort)).start()

                # if secure connection and client already connected
                else:

                    port = client_browser[client_address][1]
                    # get the route of the msgs to the specific site
                    stations_for_msg = port_stations[port][0]

                    # get the StationCom object of the first station
                    sending_client = port_stations[port][1]

                    # building a temporary ip_key list
                    ip_key_list = []
                    for i in range(len(stations_for_msg)):
                        if stations_for_msg[i] not in ip_key_dict.keys():
                            del port_stations[port]
                            del client_browser[client_address]
                            continue
                        ip_key_list.append((stations_for_msg[i], ip_key_dict[stations_for_msg[i]]))

                    # building all layers on top of the msg
                    msg = OnionServer.buildLayerAllHTTPS(msg, ip_key_list)
                    # send to the first station the msg
                    sending_client.sendMsg(msg)

            # if there is a msg to send back
            if not ret_msg_queue.empty():
                # get the ip and the msg to return
                (client_address, msg, code, port) = ret_msg_queue.get()
                #print("CLIENT ADDRESS - ", client_address, "RETMSG- ", msg, "CODE - ", code)
                if code != b'20' and code != '18':
                    print("HTTP RESPONSE CODE", code)

                if code == '18':

                    msg = "HTTP/1.1 200 Connection established\r\n\r\n"
                    client_browser[client_address] = (browserIP, port)
                    # return the msg to the client
                    proxy_server.sendMsg(client_address, msg)

                elif code == b'07' or code == "07":
                    print("Response from server - ", msg)
                    # return the msg to the client
                    proxy_server.sendMsg(client_address, msg)
                    # disconnect the client
                    proxy_server.disconnect(client_address)

                elif code == b'20':
                    proxy_server.sendMsg(client_address, msg)


def manager_comms(manager_server_q, manager_server):

    # get the station per msg number
    station_per_msg = get_station_num()

    # connect to the database
    ToriDB = DB.DB("ToriDB")
    """

    :param manager_server_q: the queue of the server that deal with manager comms
    :param server_public_key: the public key of the server
    """
    while True:
        # catch msg from server
        ip, data = manager_server_q.get()
        data = data.decode()

        # check if encrypted with sym_key before logging in
        if ip in ip_key_dict_temp.keys():
            data = ip_key_dict_temp[ip].decrypt(data)

        # check if encrypted with sym_key after logging in
        elif ip in ip_key_dict_manager.keys():
            data = ip_key_dict_manager[ip].decrypt(data).decode()

        # unpack the data
        code, msg = ServerProtocol.unpack(data)
        # the manager sent public key
        if code == '02':
            # public key of the manager
            manager_pkey = msg.encode()
            # randomizing a symetric key(string)
            sym_key = roll_key()
            # sending the manager symetric key
            msg_ret = ServerProtocol.buildSendSymetricKey(sym_key)

            # encrypting the data using the manager's public key
            msg_ret = RSAClass.encrypt_msg(msg_ret, manager_pkey)
            # send the symetric key
            manager_server.sendMsg(ip, msg_ret)
            # add the ip and the symetric key to the temp dictionary
            ip_key_dict_temp[ip] = AESClass.AESCipher(sym_key)

        # manager sent the username and password
        elif code == '08':
            username, password = msg
            # checking the username and password
            if ToriDB.checkUser(username, password):
                # return the manager 'True'
                msg_ret = ServerProtocol.buildLoginMsg("True")
                msg_ret = ip_key_dict_temp[ip].encrypt(msg_ret)
                manager_server.sendMsg(ip, msg_ret)

                # delete from temp dict and move to normal dict
                ip_key_dict_manager[ip] = ip_key_dict_temp[ip]
                del ip_key_dict_temp[ip]

                # send the client the info
                msg_ret = ServerProtocol.buildStationInfo(station_per_msg, ToriDB.send_stations())
                enc_msg = ip_key_dict_manager[ip].encrypt(msg_ret)
                manager_server.sendMsg(ip, enc_msg)

            else:
                # return the manager False
                msg_ret = ServerProtocol.buildLoginMsg("False")
                msg_ret = ip_key_dict_temp[ip].encrypt(msg_ret)
                manager_server.sendMsg(ip, msg_ret)

        # add station
        elif code == '11':
            mac = msg
            # adding the station
            ToriDB.addStation(mac)

            # send back approval
            msg_ret = ServerProtocol.buildAddOK(mac)
            enc_msg = ip_key_dict_manager[ip].encrypt(msg_ret)
            manager_server.sendMsg(ip, enc_msg)

        # delete station
        elif code == '12':
            mac = msg
            ToriDB.deleteStation(mac)

            # send back approval
            msg_ret = ServerProtocol.buildDeleteOK(mac)
            enc_msg = ip_key_dict_manager[ip].encrypt(msg_ret)
            manager_server.sendMsg(ip, enc_msg)

        # change number of station per msg
        elif code == "13":
            station_per_msg = msg
            change_station_num(station_per_msg)

            # send back approval
            msg_ret = ServerProtocol.buildChangeOK(station_per_msg)
            enc_msg = ip_key_dict_manager[ip].encrypt(msg_ret)
            manager_server.sendMsg(ip, enc_msg)


def roll_port():
    """

    :return: randomizing an unused port
    """
    found = False
    while not found:
        port = random.randint(2000, 50000)
        # check if port not in use
        if not port in port_list:
            found = True

    port_list.append(port)
    return port


def roll_key():
    """

    :return: randomizing a String for symetric key with length of 16 and returns it
    """
    # string that contains all the letters + all the digits
    l = string_c.ascii_letters + "123456789"
    string = ''

    # randomizing a 16 char long string
    for i in range(16):
        char = random.choice(l)
        string += char

    # checking if the string isn't being used already as a symetric key
    if string in symkey_list:
        return roll_key()

    else:
        # if it isn't being used , add to the symetric key list and return the key
        symkey_list.append(string)
        return string


def get_station_num():
    """

    :return: the number of station per msg (reads form the file)
    """
    with open(r"stationNum.txt", 'r') as handler:
        return int(handler.read())


def change_station_num(new_num):
    """

    :param new_num: new num to change to
    :return: changes the number of station per msg (rewrites the file)
    """

    with open(r"stationNum.txt", 'w') as handler:
        # delete the content of the file before
        handler.truncate()
        # write the new number
        handler.write(new_num)


def roll_stations():
    """

    :return: chooses 3 stations from the list and returns a list containing their ip
    """

    # returning list
    stations_for_the_msg = []

    # number of stations per msg
    count = get_station_num()
    while count > 0:
        # get a station ip from the dictionary
        ip_adr = random.choice(list(ip_key_dict.keys()))
        if ip_adr not in stations_for_the_msg:
            count = count - 1
            stations_for_the_msg.append(ip_adr)

    return stations_for_the_msg


# creating the server for comms with the stations
station_server_q = queue.Queue()
station_server = ServerComs.ServerComs(59185, station_server_q)


# creating a server for comms with manager
manager_server_q = queue.Queue()
manager_server = ServerComs.ServerComs(2028, manager_server_q)
# opening thread to deal with manager comms
threading.Thread(target=manager_comms, args=(manager_server_q, manager_server)).start()

client_browser = {} # client(address) : (browserIP, port of stations)
port_stations = {} # port : (ip of stations , StationComs of first station, client address)
ip_key_dict_temp = {}
ip_key_dict_manager = {}
ip_key_dict = {} # ip : key
ip_mac_dict = {}
symkey_list = [] # list of all sym keys
rsa_keys = RSAClass.RSAClass()
# createing the RSA keys
public_key = rsa_keys.get_public_key_pem().decode()
# station per msg
station_per_msg = get_station_num()
ToriDB = DB.DB("ToriDB")
firstSend = True

# special ports for comms with station and manager
port_list = [59185, 2028] # lists of all used ports
initialized_proxy = False

while True:
    # server for connection and change in keys with stations
    ip, data = station_server_q.get()
    data = data.decode()

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
                station_server.sendMsg(ip, msg_ret)

            else:
                print("NOT ALLOWED")
                station_server.disconnect(ip)
        # check if the communication is permitted
        if ip in ip_mac_dict:
            # station sent pkey
            if code == "02":
                station_pkey = msg.encode()
                sym_key = roll_key()
                msg_ret = ServerProtocol.buildSendSymetricKey(sym_key)
                print("SYMKEY", sym_key)
                # encrypt the symteric key with the station's public key
                encrypted = RSAClass.encrypt_msg(msg_ret, station_pkey)
                # send the symetric key
                station_server.sendMsg(ip, encrypted)
                # add the key to the dictionary
                ip_key_dict[ip] = AESClass.AESCipher(sym_key)
                station_per_msg = get_station_num()
                if len(ip_key_dict) >= station_per_msg and not initialized_proxy:
                    initialized_proxy = True

                    threading.Thread(target=proxy, args=(ip_key_dict, station_server, station_server_q, port_list, client_browser, port_stations)).start()

        else:
            # if the communication is not permitted , kick the ip off the server
            station_server.disconnect(ip)
    else:
         # put back in the queue
         station_server_q.put((ip, data.encode()))







