def buildSendMacAdr(mac):
    """

    :param mac: MAC address of station
    :return: a msg built by the protocol to send mac address
    """

    code = "00"

    msg = code + mac

    return msg


def buildPublishKeyST(Pkey):
    """

    :param Pkey: public key to publish
    :return: a msg built by the protocol to publish server's public key
    """
    code = "02"
    length = str(len(str(Pkey))).zfill(8)
    msg = code + length + str(Pkey)
    return msg


def buildOKMsg():
    """

    :return: a msg built by the protocol to return OK
    """
    return "05"


def buildSendMsgRet(msg):
    """

    :param msg: the msg to return
    :return: a msg built by the protocol to send the msg in the return route throughout the stations
    """

    code = "07"

    len_msg = str(len(msg)).zfill(8)
    if type(msg) == bytearray or type(msg) == bytes:
        msg = msg.decode()
    msg = code + len_msg + msg

    return msg


def buildSendEstablished(browserIP, browserPort):

    code = "18"

    lenIP = str(len(browserIP)).zfill(2)
    lenPort = str(len(str(browserPort))).zfill(1)

    msg = code + lenIP + browserIP + lenPort + str(browserPort)

    return msg


def unpack(msg):
    """

    :param msg: the msg to unpack
    :return: unpacks the msg according to the protocol and returns a tuple of the code and the msg
    """
    # extract msg code
    code = msg[:2]
    msg = msg[2:]
    data = ""

    if code == "01":
        length = int(msg[0:8])
        data = msg[8:length+8]

    elif code == "03":
        length = int(msg[0:2])
        data = msg[2:length+2]

    elif code == "04":
        data = msg

    elif code == "06":
        # extract first IP
        lenIP1 = int(msg[0:2])
        IP1 = msg[2:lenIP1+2]
        msg = msg[2+lenIP1: ]
        # extract second IP
        lenIP2 = int(msg[0:2])
        IP2 = msg[2:lenIP2+2]
        msg = msg[2+lenIP2: ]
        # extract the msg
        len_msg = int(msg[:8])
        new_msg = msg[8:len_msg+8]
        # asseble the data
        data = (IP1, IP2, new_msg)

    elif code == "17":
        # extract first IP
        lenIP1 = int(msg[0:2])
        IP1 = msg[2:lenIP1 + 2]
        msg = msg[2 + lenIP1:]

        # extract second IP
        lenIP2 = int(msg[0:2])
        IP2 = msg[2:lenIP2 + 2]
        msg = msg[2 + lenIP2:]

        # extract port
        lenPort = int(msg[:1])
        Port = msg[1:lenPort+1]

        msg = msg[lenPort+1:]

        # extract the msg
        lenMsg = int(msg[:8])
        new_msg = msg[8:lenMsg+8]

        data = (IP1, IP2, Port, new_msg)

    elif code == '19':
        # extract first IP
        lenIP1 = int(msg[0:2])
        IP1 = msg[2:lenIP1 + 2]
        msg = msg[2 + lenIP1:]
        # extract second IP
        lenIP2 = int(msg[0:2])
        IP2 = msg[2:lenIP2 + 2]
        msg = msg[2 + lenIP2:]
        # extract the msg
        len_msg = int(msg[:8])
        new_msg = msg[8:len_msg + 8]
        # asseble the data
        data = (IP1, IP2, new_msg)

    return (code, data)


def main():
    print(buildSendEstablished("192.168.1.11", 443))
#     print(unpack("1712192.168.4.9712192.168.4.96344300000020CONNECT TO YOUR MAMA"))
#     print(buildSendMacAdr("ff:ee:dd:cc:bb:aa"))
#     keys = RSAClass.RSAClass()
#     pkey = keys.get_public_key_pem().decode()
#     print(buildPublishKeyST(pkey))
#     print(buildOKMsg())
#     msg = "looolololololowndbvawhdvhawdbvha-jwdbjawdjawkdawjudgjawbdhjawgdygawdhawbdawdyhgawkdhawjdvh213j12321j3123213l/;,31"
#     print(SendMsgRet(msg))
#     msg ="""0100000624-----BEGIN PUBLIC KEY-----
# MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEArzPHqEIyjwetrtxxyqSw
# usIX8WcFPjc5DHKlY1TppsFK6uPJ3Li4nS0b9rsdA07RH4J1M/jf233t7tSBqdsN
# zLmcSnUfUbk4T48Utrgy7n9w/08OtMFS9JGxS6+r+xKHOfuM6iYFJxUgRDmDsFf3
# V/cuzzFie5ErTN4ha5SZoT1OYiearTNPuiBnZMjhh5rzD9CIOSx2q5TgQ6HGxBc0
# A2halTToghlUDyaL8xfPXVOAsMAFxHmjucJeF+TnxzT9BzsvyUDPfbnK0Np7NOdr
# ftmYdjNfuf5CUEJ5vPsyxXCuoEfH2UrXRYd9seQgopJb5ifCr5RcqOuhhMWA55sq
# RZVSH0Mn0iJbovNFXohwy05GBwba5rwN/Gsul66MlF8yYKVxNaltyYezPGK1LCFe
# A0ISPLSp0MEWeH26sBnbHcp9RlxvmFZnbyJ9JeAVhKdf1XrccORf3S8gXct+KB0Q
# Plprf164uDtwCptHIwkYJgTI7aMTFa6WRgHYWMytaS2bAgMBAAE=
# -----END PUBLIC KEY-----"""
#     msg = "0318example12345678901"
#     msg = "0459185"
#    print(unpack(msg))

if __name__ == "__main__":
    main()