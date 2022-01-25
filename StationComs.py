import socket
import threading
import queue


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
        print("CONNECTED")
        self.__bufferSize = 1024
        threading.Thread(target=self.__receive).start()

    def __receive(self):
        """

        :return: receives from the socket and puts in the queue of the station
        """
        while True:
            # recieve the length
            try:
                length = self.__sock.recv(8).decode()
            except Exception as e:
                print(e)
                self.__sock.close()
                break
            else:
                # connection lost
                if length == "":
                    self.__sock.close()
                    break

                # initialize the msg
                msg = bytearray()
                counter = 0
                while counter < int(length):
                    try:
                        data = self.__sock.recv(self.__bufferSize)
                    except Exception as e:
                        print(e)
                        self.__sock.close()
                        break
                    else:
                        msg.extend(data)
                        counter += len(data)
                        # got full msg
                self.__q.put(msg)

    def sendMsg(self, msg):
        """

        :param msg: the msg to send
        :return: sends the msg
        """
        if type(msg) == str:
            msg = msg.encode()
        length_msg = str(len(msg)).zfill(8).encode()
        try:
            self.__sock.send(length_msg+msg)
        except Exception as e:
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
