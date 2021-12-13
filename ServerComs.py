import socket
import select
import threading
import queue
import time


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
                        print(f'{address} - connected')
                        # add to dictionary
                        self.__users_dict[client] = address
                        self.__open_clients[address[0]] = client
                    else:
                        # receive info
                        try:
                            length = int(current_socket.recv(5).decode())
                            msg = current_socket.recv(length).decode()
                        except Exception as e:
                            print("lol finder lo yodea")
                            print(e)
                            self.disconnect(self.__users_dict[current_socket][0])
                        else:
                            # put into server queue
                            self.__serverQueue.put((self.__users_dict[current_socket][0], msg))

    def sendMsg(self, ip, msg):
        """

        :param ip: ip to send to
        :param msg: msg to send
        :return:
        """
        sock = self.__open_clients[ip]
        length = str(len(msg)).zfill(5).encode()
        if type(msg) == str:
            msg = msg.encode()
        try:
            sock.send((length+msg))
        except Exception as e:
            print(e)
            self.disconnect(ip)

    def disconnect(self, ip):
        """

        :param ip: ip address
        disconnects the socket of the ip from the server
        """

        if ip in self.__open_clients.keys():
            print(f"{self.__users_dict[self.__open_clients[ip]]} disconnected")
            self.__open_clients[ip].close()

            del self.__users_dict[self.__open_clients[ip]]
            del self.__open_clients[ip]

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


def main():
    myQ = queue.Queue()
    server = ServerComs(5918, myQ)
    data = myQ.get()
    print(data)
    server.sendMsg(data[0], data[1])


if __name__ == "__main__":
    main()
