import AESClass
import StationProtocol


def buildLayer(msg, key):
    """

    :param msg: msg to encrpyt
    :param key: key to encrypt with
    :return: build a layer on top of the msg with the key
    """
    if type(msg) == bytes:
        msg = msg.decode()
    # build by protocol
    new_msg = StationProtocol.buildSendMsgRet(msg)
    # encrypt by key
    new_msg = key.encrypt(new_msg)
    return new_msg.decode()


def remove_layer(msg, key):
    new_msg = key.decrypt(msg)
    data = StationProtocol.unpack(new_msg)
    return data


def main():

    myKey = AESClass.AESCipher("lobatuhkama")
    myKey2 = AESClass.AESCipher("lobatuhkama2")
    myKey3 = AESClass.AESCipher("lobatuhkama3")
    msg = "GET ME PIZZA"

    msg = buildLayer(msg,myKey)
    msg = buildLayer(msg, myKey2)
    msg = buildLayer(msg, myKey3)
    print(msg)
    ip = "10.0.0.7"
    lastIP = "11.0.7.110"
    enc_msg = buildLayer(msg, myKey)
    msg = myKey.decrypt(enc_msg)


if __name__ == "__main__":
    main()