import ServerProtocol
import AESClass
import StationProtocol
import sys


def buildLayer(msg, ip,lastIP, key):
    """

    :param msg: msg to move on
    :param ip: ip of next station
    :param lastIP: IP of the site
    :param key: (AESCipher) key
    :return: builds a layer on top of the msg
    """

    new_msg = ServerProtocol.buildSendMsg(msg, ip, lastIP)
    new_msg = key.encrypt(new_msg)
    return new_msg.decode()


def buildLayerConnect(msg, ip, lastIP, browserPort, key):
    """

    :param msg: msg to move on
    :param ip: ip of next station
    :param lastIP: IP of the site
    :param key: (AESCipher) key
    :return: builds a layer on top of the msg
    """

    new_msg = ServerProtocol.buildConnectMsg(ip, lastIP, browserPort, msg)
    new_msg = key.encrypt(new_msg)
    return new_msg.decode()


def buildLayerHTTPS(msg, key):
    """

    :param msg: msg to deliver
    :param key: symetric key of station
    :return: builds protocol msg for sending https msg and encrypts the data
    """
    new_msg = ServerProtocol.buildSendMsgHTTPS(msg)
    new_msg = key.encrypt(new_msg)
    return new_msg.decode()


def removeLayer(msg, key):
    """

    :param msg: encrypted msg
    :param key: key to decrypt msg
    :return: removes a layer off the msg
    """
    new_msg = key.decrypt(msg)
    data = ServerProtocol.unpack(new_msg)
    return data


def removeLayerAll(msg, key_list):
    """

    :param msg: the msg
    :param key_list: list of keys to decrypt the msg (must be in order)
    :return: removes all the layer from the msg
    """
    count = len(key_list)
    for key in reversed(key_list):
        try:
            code, msg = removeLayer(msg, key)
        except:
            sys.exit()

        if code == "18":
            msg = msg[2]

        count = count - 1

    return (code, msg)


def buildLayerAll(msg, ip_key_list, lastIP):
    """

    :param msg: msg to encrypt
    :param ip_key_list: list of tuples that have (ip, key)
    :param lastIP: ip of site
    :return: builds all the layers of the msg by all the ips and keys
    """
    # last station enryption go first
    data = buildLayer(msg, lastIP, lastIP, ip_key_list[len(ip_key_list)-1][1])
    # build all the layers except the first and last station
    for index in range(len(ip_key_list)-2, 0, -1):
        # build layer
        data = buildLayer(data, ip_key_list[index+1][0], lastIP, ip_key_list[index][1])
    # first station encryption goes last
    data = buildLayer(data, ip_key_list[1][0], lastIP, ip_key_list[0][1])

    return data


def buildLayerAllConnect(msg, ip_key_list, lastIP, broswerPort):
    """

   :param msg: msg to encrypt
   :param ip_key_list: list of tuples that have (ip, key)
   :param lastIP: ip of site
   :return: builds all the layers of the msg by all the ips and keys
   """

    # last station enryption go first
    data = buildLayerConnect(msg, lastIP, lastIP, broswerPort, ip_key_list[len(ip_key_list) - 1][1])
    # build all the layers except the first and last station
    for index in range(len(ip_key_list) - 2, 0, -1):
        # build layer
        data = buildLayerConnect(data, ip_key_list[index + 1][0], lastIP, broswerPort, ip_key_list[index][1])
    # first station encryption goes last
    data = buildLayerConnect(data, ip_key_list[1][0], lastIP, broswerPort, ip_key_list[0][1])

    return data


def buildLayerAllHTTPS(msg, ip_key_list):
    """

    :param msg: msg to build layers on
    :param ip_key_list: list of tuples that have (ip, key)
    :return: builds all the layers of the msg by all the ips and keys for https
    # """

    # last station enryption go first
    data = buildLayerHTTPS(msg, ip_key_list[len(ip_key_list) - 1][1])
    # build all the layers except the first and last station
    for index in range(len(ip_key_list) - 2, 0, -1):
        # build layer
        data = buildLayerHTTPS(data, ip_key_list[index][1])
    # first station encryption goes last
    data = buildLayerHTTPS(data, ip_key_list[0][1])

    return data


def main():
    pass
    myKey = AESClass.AESCipher("lobatuhkama")
    myKey2 = AESClass.AESCipher("lobatuhkama2")
    myKey3 = AESClass.AESCipher("lobatuhkama3")
    msg = "CONNECT ME PIZZA"

    ip1 = "192.168.1.1"
    ip2 = "192.168.1.2"
    ip3 = "192.168.1.3"
    last_ip = "188.188.1.12"
    print(buildLayerConnect(msg, ip1, last_ip, 443, myKey))
    ip_key_list = [(ip1, myKey), (ip2, myKey2), (ip3, myKey3)]

    print(buildLayerAllConnect(msg, ip_key_list, last_ip, 443))
    # # ip = "10.0.0.7"
    # # lastIP = "11.0.7.110"
    # # enc_msg = buildLayer(msg, ip, lastIP, myKey)
    # # print(enc_msg)
    # msg = "1ruG/yRSMqGkXfiDgCfIUPg2W6nUI0GOT6ijFE9iOpURSDSSVRlYCQNlZl9fb96VNo8/DHoInm00QnuAEJlz+4H5SBPs+YlHQoyM9wEKnPFxlsMvtYjkaQDWiFznkCE82P35wK9MjDeAAOZLU2nYpE2A9MCElrYYVAq9VmNP8V8BA/86i5fMaAbjUPcgkcLixAOb86qB/lE3X8eSS1Trww=="
    # key_list = [myKey3,myKey2,myKey]
    # print(removeLayerAll(msg, key_list))


if __name__ == "__main__":
    main()