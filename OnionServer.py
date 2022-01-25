import ServerProtocol
import AESClass
import StationProtocol


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


def removeLayer(msg, key):
    """

    :param msg: encrypted msg
    :param key: key to decrypt msg
    :return: the msg
    """
    new_msg = key.decrypt(msg)
    data = ServerProtocol.unpack(new_msg)
    return data[1]


def removeLayerAll(msg, key_list):
    """

    :param msg: the msg
    :param key_list: list of keys to decrypt the msg (must be in order)
    :return:
    """

    for key in reversed(key_list):
        msg = removeLayer(msg, key)

    return msg


def buildLayerAll(msg,ip_key_list, lastIP):
    """

    :param msg: msg to encrypt
    :param ip_key_list: list of tuples that have (ip, key)
    :param lastIP: ip of site
    :return: builds all the layers of the msg by all the ips and keys
    """
    # last station enryption go first

    data = buildLayer(msg, lastIP, lastIP, ip_key_list[len(ip_key_list)-1][1])
    # build all the layers except the first and last station
    for index in range(len(ip_key_list)-2,0,-1):
        # build layer
        data = buildLayer(data, ip_key_list[index+1][0], lastIP, ip_key_list[index][1])
    # first station encryption goes last
    data = buildLayer(data, ip_key_list[1][0], lastIP, ip_key_list[0][1])

    return data


def main():
    pass
    # myKey = AESClass.AESCipher("lobatuhkama")
    # myKey2 = AESClass.AESCipher("lobatuhkama2")
    # myKey3 = AESClass.AESCipher("lobatuhkama3")
    # msg = "GET ME PIZZA"
    # # ip = "10.0.0.7"
    # # lastIP = "11.0.7.110"
    # # enc_msg = buildLayer(msg, ip, lastIP, myKey)
    # # print(enc_msg)
    # msg = "1ruG/yRSMqGkXfiDgCfIUPg2W6nUI0GOT6ijFE9iOpURSDSSVRlYCQNlZl9fb96VNo8/DHoInm00QnuAEJlz+4H5SBPs+YlHQoyM9wEKnPFxlsMvtYjkaQDWiFznkCE82P35wK9MjDeAAOZLU2nYpE2A9MCElrYYVAq9VmNP8V8BA/86i5fMaAbjUPcgkcLixAOb86qB/lE3X8eSS1Trww=="
    # key_list = [myKey3,myKey2,myKey]
    # print(removeLayerAll(msg, key_list))


if __name__ == "__main__":
    main()