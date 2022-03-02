import socket
import select
import threading
import queue


class ServerComs(object):
    def __init__(self, port, serverQueue):
        """

        :param port: port to listen on
        :param serverQueue: queue of server
        """
        self.__port = port
        self.__serverQueue = serverQueue
        self.__users_dict = {} # socket: (port, ip)
        # create the server socket and listen
        self.__serverSock = socket.socket()
        self.__serverSock.bind(('0.0.0.0', self.__port))
        self.__serverSock.listen(3)
        self.__open_clients = {} # ip:socket
        self.__bufferSize = 1024
        self.__receiving = True
        threading.Thread(target=self.__receive).start()

    def __receive(self):
        """

        :return: receives from the socket and puts the info in the queue as (IP, msg)
        """
        while self.__receiving:
            try:
                rlist, wlist, xlist = select.select(list(self.__users_dict.keys()) + [self.__serverSock], [], [], 0.3)
            except:
                pass
            else:
                for current_socket in rlist:
                    if current_socket is self.__serverSock:
                        # new client
                        client, address = self.__serverSock.accept()
                        print(address, "- CONNECTED")

                        # add to dictionary
                        self.__users_dict[client] = address
                        self.__open_clients[address[0]] = client
                    else:
                        # receive info
                        try:
                            # receive length of msg
                            length = current_socket.recv(8).decode()
                        except Exception as e:
                            print(e)
                            if current_socket in self.__users_dict.keys():
                                self.disconnect(self.__users_dict[current_socket][0])
                            break

                        else:
                            # disconnected
                            if length == '':
                                self.disconnect(self.__users_dict[current_socket][0])
                            else:
                               # initiate msg
                                msg = bytearray()
                                counter = 0
                                # receive the msg
                                while counter < int(length):
                                    if (int(length) - counter) > self.__bufferSize:
                                        try:
                                            data = current_socket.recv(self.__bufferSize)
                                        except Exception as e:
                                            print(e, 2)
                                            self.disconnect(self.__users_dict[current_socket][0])
                                        else:
                                            if data == b'':
                                                self.disconnect(self.__users_dict[current_socket][0])
                                                msg = b''
                                                break
                                            else:
                                                msg.extend(data)
                                                counter += len(data)

                                    else:
                                        try:
                                            data = current_socket.recv((int(length) - counter))
                                        except Exception as e:
                                            print(e, 2)
                                            self.disconnect(self.__users_dict[current_socket][0])
                                        else:
                                            if data == b'':
                                                self.disconnect(self.__users_dict[current_socket][0])
                                                msg = b''
                                                break
                                            else:
                                                msg.extend(data)
                                                counter += len(data)
                                if msg != b'':
                                    self.__serverQueue.put((self.__users_dict[current_socket][0], msg))

    def sendMsg(self, ip, msg):
        """

        :param ip: ip to send to
        :param msg: msg to send
        :return:
        """
        if ip in self.__open_clients.keys():
            sock = self.__open_clients[ip]
            if type(msg) == str:
                msg = msg.encode()
            length = str(len(msg)).zfill(8).encode()
            try:
                sock.send(length+msg)
            except Exception as e:
                print(e,1)
                self.disconnect(ip)

    def disconnect(self, ip):
        """

        :param ip: ip address
        disconnects the socket of the ip from the server
        """
        if ip in self.__open_clients.keys():
            print(f"{self.__users_dict[self.__open_clients[ip]]} disconnected")
            self.__open_clients[ip].close()
            try:
                del self.__users_dict[self.__open_clients[ip]]
                del self.__open_clients[ip]
            except:
                pass
            else:
                print("DC, IP-", ip)
                self.__serverQueue.put((ip, f"dc"))

    def close_server(self):
        """
        closes the server
        """
        sockets = self.__open_clients.values()
        try:
            for sock in sockets:
                try:
                    sock.close()
                except:
                    pass
        except:
            pass
        self.__receiving = False
        self.__serverSock.close()


def main():
    myQ = queue.Queue()
    server = ServerComs(5918, myQ)
    data = myQ.get()
    server.sendMsg(data[0], data[1])


if __name__ == "__main__":
    main()
