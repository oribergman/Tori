import socket
import threading
import queue
import select


class ProxyComs(object):
    def __init__(self, port, serverQueue):
        """

        :param port: port to listen on
        :param serverQueue: queue of server
        """
        self.__port = port
        self.__serverQueue = serverQueue
        self.__users_dict = {}  # socket: (port, ip)
        # create the server socket and listen
        self.__serverSock = socket.socket()
        self.__serverSock.bind(('0.0.0.0', self.__port))
        self.__serverSock.listen(1)
        self.__open_clients = {}  # (ip,port):socket
        self.__bufferSize = 1024
        threading.Thread(target=self.__receive).start()

    def __receive(self):
        """

        :return: receives from the socket and puts the info in the queue as (IP, msg)
        """
        while True:
            try:
                rlist, wlist, xlist = select.select(list(self.__users_dict.keys()) + [self.__serverSock], [], [], 0.3)
            except:
                pass
            else:
                for current_socket in rlist:
                    if current_socket is self.__serverSock:
                        # new client
                        client, address = self.__serverSock.accept()

                        # add to dictionary
                        self.__users_dict[client] = address
                        self.__open_clients[address] = client
                    else:
                        # receive info
                        receiving = True
                        msg = bytearray()
                        while receiving:
                            try:
                                data = current_socket.recv(self.__bufferSize)
                            except Exception as e:
                                if current_socket in self.__users_dict.keys():
                                    self.disconnect(self.__users_dict[current_socket])

                                else:
                                    current_socket.close()
                                break
                            else:
                                msg.extend(data)
                                # got the full msg
                                if len(data) < self.__bufferSize:
                                    receiving = False

                        if len(msg) == 0:
                            if current_socket in self.__users_dict.keys():
                                self.disconnect(self.__users_dict[current_socket])
                        else:
                            # put into server queue
                            self.__serverQueue.put((self.__users_dict[current_socket], msg))

    def sendMsg(self, address, msg):
        """

        :param ip: ip to send to
        :param msg: msg to send
        :return: sends the msg to the ip and true if done
        """
        flag = True # if the msg has been sent
        if address in self.__open_clients.keys():
            sock = self.__open_clients[address]
            if type(msg) == str:
                msg = msg.encode()

            try:
                sock.send(msg)
            except Exception as e:
                print(e,4)
                self.disconnect(address)
        else:
            flag = False
        return flag

    def disconnect(self, address):
        """

        :param ip: ip address
        disconnects the socket of the ip from the server
        """
        if address in self.__open_clients.keys():
            try:
                self.__open_clients[address].close()
                del self.__users_dict[self.__open_clients[address]]
                del self.__open_clients[address]

            except Exception as e:
                print("E-", e)

    def close_server(self):
        """
        closes the server
        """
        for sock in self.__open_clients.values():
            try:
                sock.close()
            except:
                pass

        self.__serverSock.close()

