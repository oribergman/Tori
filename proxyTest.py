import socket
import select
import threading
import AESClass

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


def httpGet(address, current_socket, msg):
    try:
        browserIP = socket.gethostbyname(address)
    except:
        disconnect(users_dict[current_socket])
    else:
        # connect to the site
        browserSocket = socket.socket()
        try:
            browserSocket.connect((browserIP, 80))
        except:
            disconnect(users_dict[current_socket])
        else:
            if type(msg) == str:
                msg = msg.encode()
            browserSocket.send(msg)
            receive(browserSocket, users_dict[current_socket])


def receive(socket_to_site, address):
    # create the socket connection to the site
    print("GOT HTTP ADDRESS", address)
    msg = bytearray()
    while True:
        rlist, wlist, xlist = select.select([socket_to_site], [], [])
        if rlist:
            data = socket_to_site.recv(1024)
            if data == b'':
                break
            msg.extend(data)
        else:
            break
    print("BLA BLA BLA", msg)
    sendMsg(address, msg)


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
                        if current_browser in browsers_clients and browsers_clients[current_browser] in waiting_clients:
                            del waiting_clients[browsers_clients[current_browser]]
                            del browsers_clients[current_browser]
                        elif current_browser in browsers_clients:
                            print(browsers_clients.keys())
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
sym_key = AESClass.AESCipher("123")
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
                # print(f'{address} - connected to proxy')
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

                    # print("GOT FROM CLIENT", msg)
                    if current_socket in waiting_clients.keys():
                        # sending  the data from client to browser
                        waiting_clients[current_socket].send(msg)

                    else:
                        msg = msg.decode()
                        msgSplit = msg.split()
                        if len(msgSplit) > 1:
                            address = msgSplit[1]

                            if msg.startswith('CONNECT'):
                                if address.split(':')[1].isnumeric():
                                    browserLink, browserPort = address.split(':')
                                    browserPort = int(browserPort)
                                    try:
                                        browserIP = socket.gethostbyname(browserLink)
                                    except:
                                        print("FAILED", browserLink)
                                    address = (browserIP, browserPort)
                                    # connect to the site
                                    browserSocket = socket.socket()

                                    try:
                                        browserSocket.connect((browserIP, browserPort))
                                    except:
                                        disconnect(users_dict[current_socket])
                                    else:
                                        waiting_clients[current_socket] = browserSocket
                                        browsers_clients[browserSocket] = current_socket
                                        msg_ret = "HTTP/1.1 200 Connection established\r\n\r\n"
                                        sendMsg(users_dict[current_socket], msg_ret)
                                else:
                                    disconnect(users_dict[current_socket])

                            elif msg.startswith('POST') or msg.startswith('GET') or msg.startswith("HEAD") or msg.startswith("PUT") or msg.startswith("DELETE") or msg.startswith("OPTIONS"):
                                address = msg.split('/')[2]
                                threading.Thread(target=httpGet, args= (address, current_socket, msg)).start()

                            else:
                                disconnect(users_dict[current_socket])



