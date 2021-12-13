import socket
import threading
import queue
import time


class StationComs(object):
    def __init__(self, port, ip, q):
        """

        :param port: port to connect on
        :param ip: ip to connect to
        :param q: queue of the station
        constructor to stationComs
        """
        self.__port = port
        self.__ip = ip
        self.__q = q
        self.__sock = socket.socket()
        self.__sock.connect((self.__ip, self.__port))
        threading.Thread(target=self.__receive).start()

    def __receive(self):
        """

        :return: receives from the socket and puts in the queue of the station
        """
        while True:
            try:
                length = self.__sock.recv(5).decode()
                msg = self.__sock.recv(int(length))
            except Exception as e:
                print(e)
                self.__sock.close()
                break
            else:
                self.__q.put(msg)

    def sendMsg(self, msg):
        """

        :param msg: the msg to send
        :return: sends the msg
        """
        length = str(len(msg)).zfill(5).encode()
        if type(msg) == str:
            msg = msg.encode()
        try:
            self.__sock.send(length+msg)
        except Exception as e:
            pass
            print(1)
            print(e)
            self.__sock.close()


def main():
    pass
    # myQ = queue.Queue()
    # st = StationComs(5918, "127.000.000.001", myQ)
    # st.sendMsg("Hey")
    # print(myQ.get())
if __name__ == "__main__":
    main()
