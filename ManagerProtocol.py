
def buildPublishPKeyMA(Pkey):
    """

    :param Pkey: public key to publish
    :return: a msg built by the protocol to publish manager's public key
    """

    code = "02"
    length = str(len(str(Pkey))).zfill(8)
    msg = code + length + str(Pkey)
    return msg


def buildSendUserAndPassword(username, password):
    """

    :param username: username
    :param password: password
    :return: a msg built by the protocol to send manager's username and password
    """

    code = "08"
    len_user = str(len(username)).zfill(2)
    len_password = str(len(password)).zfill(2)

    msg = code + len_user + username + len_password + password

    return msg


def buildAddStationMsg(mac):
    """

    :param mac: MAC address of station
    :return: a msg built by the protocol to send to the server to add a station
    """

    code = "11"

    msg = code + mac

    return msg


def buildDeleteStationMsg(mac):
    """

    :param mac: MAC address of station
    :return: a msg built by the protocol to send to the server to delete a station
    """

    code = "12"

    msg = code + mac

    return msg


def buildChNumOfStations(num):
    """

    :param mac: MAC address of station
    :return: a msg built by the protocol to send to the server to change the number of stations per msg
    """

    code = "13"

    num = str(num)

    msg = code + num

    return msg


def buildAskForNumOfStations():
    """

    :return: a msg built by the protocol to send to the server to give the current the number of stations per msg
    """
    code = "14"

    msg = code

    return msg


def unpack(msg):
    """

    :param msg: msg to unpack
    :return: unpacks the msg according to the protocol and returns a tuple of the code and the msg
    """
    print(msg)
    # extract msg code
    code = msg[:2]
    msg = msg[2:]
    data = ""

    # sent public key
    if code == "01":
        length = int(msg[0:8])
        data = msg[8:length + 8]

    elif code == "03":
        length = int(msg[0:2])
        data = msg[2:length + 2]

    elif code == "09":
        length = int(msg[0:1])
        data = msg[1:length+1]

    elif code == "10":
        # extract stations per msg argument
        station_per_msg = msg[0]
        msg = msg[1:]

        station_list = []
        # get all the lists
        while msg != "":
            station_list.append(msg[:17])
            msg = msg[17:]

        # organize the data
        data = (station_per_msg, station_list)

    elif code == "15":
        data = msg

    return (code, data)


def main():
    pass
    # username = "admin"
    # password = "admin123"
    # print(buildSendUserAndPassword(username, password))
    msg = "105ff:e6:1f:21:a5:b0ff:e6:1f:21:a5:b1ff:e6:1f:21:a5:b2"
    print(unpack(msg))
    # num_of_stations = 3
    # print(buildChNumOfStations(num_of_stations))
    # msg = "094True"
    # msg = "1009192.1.1.810193.2.2.303ff:e6:1f:21:a5:b0ff:e6:1f:21:a5:b1ff:e6:1f:21:a5:b259185"
    # print(unpack(msg))

if __name__ == "__main__":
    main()