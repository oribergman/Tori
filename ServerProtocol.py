import RSAClass


def buildPublishPKeySE(Pkey):
    """

    :param Pkey: public key to publish
    :return: a msg built by the protocol to publish server's public key
    """
    code = "01"
    length = str(len(str(Pkey))).zfill(8)
    msg = code + length + str(Pkey)
    return msg


def buildSendSymetricKey(sym_key):
    """

    :param sym_key: String symetric key
    :return: a msg built by the protocol to send symetric key
    """

    code = "03"
    length = str(len(str(sym_key))).zfill(2)

    msg = code + length + str(sym_key)

    return msg


def buildSendPort(port):
    """

    :param port: port number to send
    :return: a msg built by the protocol to send port number
    """

    code = "04"

    msg = code + str(port).zfill(5)

    return msg


def buildSendMsg(msg, passto, lastip):
    """

    :param msg: encrypted msg (String)
    :param passto: IP address of who to pass on
    :param lastip: IP address of the site
    :return: a msg built by the protocol to send the msg throughout the stations
    """
    if type (msg) == bytes:
        msg = msg.decode()
    code = "06"
    lenIP1 = str(len(passto)).zfill(2)
    lenIP2 = str(len(lastip)).zfill(2)
    length_msg = str(len(msg)).zfill(8)
    new_msg = code + lenIP1 + passto + lenIP2 + lastip + length_msg + msg

    return new_msg


def buildLoginMsg(isTrue):
    """

    :param isTrue: True or False rather if the password is correct
    :return: a msg built by the protocol to send back to manager if the password is correct
    """

    code = "09"
    length = str(len(str(isTrue)))

    msg = code + length + str(isTrue)

    return msg


def buildStationInfo(stations_per_msg, stations):
   """

   :param stations_per_msg: the station per msg
   :param stations: all the stations
   :return: msg build by the protocol to give info for the manager about the stations
   """

   code = "10"

   msg = code + str(stations_per_msg)

   # add the stations's mac to msg
   for mac in stations:
       msg += mac

   return msg


def buildChangeOK(current_num):
    """
    ;:param current_num: the current num of stations per msg
    :return: msg build by the protocol to give the manager the approval that the number changed
    """
    code = "14"

    msg = code + current_num

    return msg

def buildAddOK(mac):
    """
    :param mac: mac address of station to add
    :return: msg build by the protocol to give the manager the approval that the station had been added
    """

    code = "15"

    msg = code + mac

    return msg


def buildDeleteOK(mac):
    """
    :param mac: mac address of station to delete

    :return: msg build by the protocol to give the manager the approval that the station had been deleted
    """

    code = "16"

    msg = code + mac

    return msg


def buildConnectMsg(clientIP, browserIP, browserPort, msg):
    """

    :param clientIP: the ip of the client
    :param browserPort: the port to connect on
    :param browserIP: browser
    :return: msg build by the protocol to send a msg from the CONNECT method
    """

    code = "17"

    lenIP1 = str(len(clientIP)).zfill(2)
    lenIP2 = str(len(browserIP)).zfill(2)
    lenPort = str(len(str(browserPort))).zfill(1)
    lenMsg = str(len(msg)).zfill(8)

    ret_msg = code + lenIP1 + clientIP + lenIP2 + browserIP + lenPort + str(browserPort) + lenMsg + msg

    return ret_msg


def buildSendMsgHTTPS(msg):
    if type(msg) == str:
        msg = msg.encode()

    code = b'19'

    lenMsg = str(len(msg)).zfill(8)

    msg = code + lenMsg.encode() + msg

    return msg


def unpack(msg):
    """

   :param msg: the msg to unpack
   :return: unpacks the msg according to the protocol and returns a tuple of the code and the msg
    """

    code = msg[:2]
    msg = msg[2:]
    data = ""

    if code == b'20':
        lenMsg = int(msg[0:8].decode())
        data = msg[8:8+lenMsg]
    elif type(msg) == bytes:
        code = code.decode()
        msg = msg.decode()
    # sent mac address
    if code == "00":
        data = msg

    # sent public key
    elif code == "02":
        length = int(msg[0:8])
        data = msg[8:length+8]
    # ok msg
    elif code == "05":
        data = ""

    # returning packet msg
    elif code == "07":
        length = int(msg[0:8])
        data = msg[8:length + 8]

    # username and password from manager
    elif code == "08":

        # extract user
        len_user = int(msg[:2])
        user = msg[2:2+len_user]
        msg = msg[2+len_user:]

        # extract password
        len_password = int(msg[:2])
        password = msg[2:2 + len_password]

        data = (user, password)
    # add or remove station + changing number of station per msg
    elif code == "11" or code == "12" or code == "13":
        data = msg

    elif code == "18":
        # extract first IP
        lenIP1 = int(msg[0:2])
        IP1 = msg[2:lenIP1 + 2]
        msg = msg[2 + lenIP1:]

        # extract port
        lenPort = int(msg[:1])
        Port = msg[1:lenPort + 1]

        msg = msg[lenPort +1 :]

        lenMsg = int(msg[0:8])
        msg = msg[8: 8+lenMsg]

        # len msg
        data = (IP1, Port, msg)

    elif code == b'20':
        lenMsg = int(msg[0:8].decode())
        data = msg[8:8+lenMsg]

    return (code, data)


def main():
    print(buildSendMsgHTTPS(bytearray(b'\\xzawad\\awdawd\\wdad')))
    print(unpack(b'2000000019\\xzawad\\awdawd\\wdad'))
#     print(buildConnectMsg("192.168.4.97", "192.168.4.96", 443, "CONNECT TO YOUR MAMA"))
#     keys = RSAClass.RSAClass()
#     pkey = keys.get_public_key_pem().decode()
#     print(buildPublishPKeySE(str(pkey)))
#     sym_key = "example12345678901"
#     print(buildSendSymetricKey(sym_key))
#     port = 5185
#     print(buildSendPort(port))
#    firstIP = "192.1.1.8"
#    lastIP = "193.2.2.30"
#     msg = "xdxdxdxdxdxdolololololololoololololololololololololololoololool"
#     print(buildSendMsg(msg, firstIP, lastIP))
#     station_per_msg = 5
#     stations = ["ff:e6:1f:21:a5:b0", "ff:e6:1f:21:a5:b1", "ff:e6:1f:21:a5:b2"]
#     print(buildStationInfo(station_per_msg, stations))
#    print(buildRealTimeInfo(firstIP, lastIP, stations, port))
#     msg = "00ff:ee:dd:cc:bb:aa"
#     msg = """0200000624-----BEGIN PUBLIC KEY-----
# MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAvBAxSmkZ4G8LmU/5KXhN
# bk93d3TtWbwFvYHXlX/EbYLzptKSHWzAXB/GkArsPL41KdMYxuI6DuqlRm+h0ioe
# wlNYMkfKf7BT6mewB8lX887ZchTc+A4bQZh6QXJsd6VExbMkzKBAoMGqwDmTfPK/
# L2Hn7Upkn4jWessfSJAJNpYo/XY+hNyfrLuEZ1W4ysPN0PPU3vZGddre/8VKRc8G
# DezgZV5Sm8/cJEXzPH06OtxasPLrEo/cAQUiVAgKgkrBqfU9g0xPb1bmb6H1gkzR
# tgdTTkN/MATl3nzNuKPta7EzTI4KjuiVZ0uqsKSnooSTDTei3BTIWBJzBwJ6U+HK
# qaR0HjoNEuQXUtsd6dJ8FgUoPbV3cwKzVb26DoC8hhUodhI04msqTkMVjkiweV+i
# GK0gtC2Is3sFeRgo1AuVi5wJ8C6Yr4rueaNf1KpzjKyGJHTPhGqRkcOuEE6jr6xs
# OoboHQuS4PIyKE9zJyFao9bHd1n93Ib45kvUifsuh2jPAgMBAAE=
# -----END PUBLIC KEY-----"""
#    msg = "05"
#    msg = "0700000113looolololololowndbvawhdvhawdbvha-jwdbjawdjawkdawjudgjawbdhjawgdygawdhawbdawdyhgawkdhawjdvh213j12321j3123213l/;,31"
#    msg = "0805admin08admin123"
#    msg = "11ff:ee:dd:cc:bb:aa"
#    msg = "12ff:ee:dd:cc:bb:aa"
#    msg = "133"
#
#     print(unpack(msg))


if __name__ == "__main__":
    main()
