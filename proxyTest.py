import socket
import select
import threading


def disconnect(address):
    """

    :param ip: ip address
    disconnects the socket of the ip from the server
    """
    if address in open_clients.keys():
        try:
            print(f"{address} disconnected")
            open_clients[address].close()
            del users_dict[open_clients[address]]
            del open_clients[address]

        except Exception as e:
            print("E-", e)


def sendMsg(address, msg):
    """

    :param ip: ip to send to
    :param msg: msg to send
    :return: sends the msg to the ip
    """
    if address in open_clients.keys():
        sock = open_clients[address]
        if type(msg) == str:
            msg = msg.encode()
        print("SENDING TO CLIENT - ", msg)
        try:
            sock.send(msg)
        except Exception as e:
            print(e, 4)
            disconnect(address)
    else:
        print("not found the address", "address = " + str(address))


def browserCom():
    while True:
        try:
            rlist, wlist, xlist = select.select(list(browsers_clients.keys()), [], [], 0.3)
        except:
            pass
        else:
            for current_browser in rlist:
                # receive data from the browser
                receiving = True
                resp_msg = bytearray()
                while receiving:
                    try:
                        data = current_browser.recv(1024)
                    except Exception as e:
                        print(e)
                        del waiting_clients[browsers_clients[current_browser]]
                        current_browser.close()
                        browsers_clients[current_browser].close()
                        del browsers_clients[current_browser]

                    else:
                        resp_msg.extend(data)
                        # got the full msg
                        if len(data) < 1024:
                            receiving = False
                # disconnecting browser
                if resp_msg != bytearray(b''):
                    print("RESPONSE FROM BROWSER", resp_msg)
                #     del waiting_clients[browsers_clients[current_browser]]
                #     current_browser.close()
                #     browsers_clients[current_browser].close()
                #     del browsers_clients[current_browser]
                #     print("DISCONNECTING")

                    # sending the msg to the client
                    if current_browser in browsers_clients and browsers_clients[current_browser] in users_dict:
                        sendMsg(users_dict[browsers_clients[current_browser]], resp_msg)


serverSock = socket.socket()
serverSock.bind(('0.0.0.0', 8080))
serverSock.listen(3)
waiting_clients = {} # client : browser
users_dict = {}
open_clients = {}
browsers_clients = {} # browser : client

threading.Thread(target=browserCom).start()
while True:
    try:
        rlist, wlist, xlist = select.select(list(users_dict.keys()) + [serverSock], [], [], 0.3)
    except:
        pass
    else:
        for current_socket in rlist:
            if current_socket is serverSock:
                # new client
                client, address = serverSock.accept()
                print(f'{address} - connected to proxy')
                # add to dictionary
                users_dict[client] = address
                open_clients[address] = client
            else:
                # receive info
                receiving = True
                msg = bytearray()
                while receiving:
                    try:
                        data = current_socket.recv(1024)
                    except Exception as e:
                        print(e, 3)
                        if current_socket in users_dict.keys():
                            disconnect(users_dict[current_socket])

                        else:
                            current_socket.close()
                        break
                    else:
                        msg.extend(data)
                        # got the full msg
                        if len(data) < 1024:
                            receiving = False
                if len(msg) == 0:
                    if current_socket in users_dict.keys():
                        disconnect(users_dict[current_socket])
                else:

                    print("GOT FROM CLIENT", msg)
                    if current_socket in waiting_clients.keys():
                        # sending  the data from client to browser
                        waiting_clients[current_socket].send(msg)

                    else:
                        msg = msg.decode()
                        msgSplit = msg.split()
                        address = msgSplit[1]

                        if address.split(':')[1].isnumeric():
                            if msg.startswith('CONNECT'):
                                browserLink, browserPort = address.split(':')
                                browserPort = int(browserPort)
                                browserIP = socket.gethostbyname(browserLink)
                                address = (browserIP, browserPort)
                                # connect to the site
                                browserSocket = socket.socket()
                                print(address)
                                try:
                                    browserSocket.connect((browserIP, browserPort))
                                except:
                                    disconnect(users_dict[current_socket])
                                else:
                                    waiting_clients[current_socket] = browserSocket
                                    browsers_clients[browserSocket] = current_socket
                                    msg_ret = "HTTP/1.1 200 Connection established\r\n\r\n"
                                    sendMsg(users_dict[current_socket], msg_ret)

                            elif msg.startswith('POST') or msg.startswith('GET'):
                                browserLink, browerPort = address.split(':')
                                browerPort = int(browerPort)
                                browserIP = socket.gethostbyname(browserLink)
                                # connect to the site
                                browserSocket = socket.socket()
                                print(address)
                                browserSocket.connect((browserIP, browerPort))
                                browserSocket.send(msg)

                                # receive response
                                resp_msg = bytearray()
                                while True:
                                    rlist, wlist, xlist = select.select([browserSocket], [], [])
                                    if rlist:
                                        data = browserSocket.recv(1024)
                                        if data == b'':
                                            break
                                        resp_msg.extend(data)
                                    else:
                                        break
                                print("GOT RESP", resp_msg)
                                sendMsg(users_dict[current_socket], resp_msg)

                            else:
                                disconnect(users_dict[current_socket])



