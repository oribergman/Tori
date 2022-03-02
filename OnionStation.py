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


def buildLayerHTTPS(msg, key):
    """

    :param msg: the msg to forward
    :param key: symetric key for encrypt
    :return:  :return: builds a msg according to the protocol of the returning https msg and encrypts
    """
    new_msg = StationProtocol.buildSendHTTPS(msg)
    new_msg = key.encrypt(new_msg)
    return new_msg.decode()


def buildLayerConnect(browserIP, browserPort, key, msg):
    """

    :param browserIP: IP of the browser
    :param browserPort: port of the browser
    :param key: symetric key for encrypt
    :param msg: the msg to forward
    :return: builds a msg according to the protocol of the returning connect msg and encrypts
    """
    new_msg = StationProtocol.buildSendEstablished(browserIP, browserPort, msg)
    new_msg = key.encrypt(new_msg)
    return new_msg.decode()


def remove_layer(msg, key):
    """

    :param msg: msg to remove layer from
    :param key: the key to decrypt the data with
    :return: the msg after the decryption and after the protocol translation
    """
    new_msg = key.decrypt(msg).decode()
    new_msg = StationProtocol.unpack(new_msg)
    return new_msg


def main():

    myKey = AESClass.AESCipher("lobatuhkama")
    myKey2 = AESClass.AESCipher("lobatuhkama2")
    myKey3 = AESClass.AESCipher("lobatuhkama3")
    msg = "lhnJlnvs6EFOKRdptLXelpEliHanymsEq8Nay1oocpDJSRw6VlewwsZOOsEMcEU9mxxiic1h8IRALt0E9iAYTdSU1PgUSgL1PmEP+Pr3ramrbpyRQAzzMp5sEMZcXc6v0C9duFF2DRN4jCr+q+gk5w8Rqx2ypsYATcAg3JN172rLE2O15t5RZBkwEKIA1o1zblvs+znwJ+90KJE4OE5Rt0gisEXtOM3+35EAFYOOskIKY2w4oKk59Vm9zE4JploQDWzxoE1++Ym+AlrKmDHnHEaBokbQrkjz1I0tNaZvSkg7dPTQJJdij9cfk71tLUhYHLEgvoxmnJ3/EGvJWniO6B/iZwzPGX2yQqKZVLkUN7d41Er2LuiJSZNSATf/oOnp0YrxMf06J+dnMxtFqAVNcg=="
    data1 = remove_layer(msg, myKey)

    data2 = remove_layer(data1[1][3], myKey2)

    data3 = remove_layer(data2[1][3], myKey3)
    print(data3)
    # msg = buildLayer(msg,myKey)
    # msg = buildLayer(msg, myKey2)
    # msg = buildLayer(msg, myKey3)
    # print(msg)
    # ip = "10.0.0.7"
    # lastIP = "11.0.7.110"
    # enc_msg = buildLayer(msg, myKey)
    # msg = myKey.decrypt(enc_msg)


if __name__ == "__main__":
    main()