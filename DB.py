import sqlite3
import hashlib


class DB(object):
    def __init__(self, DB_name):
        """

        :param DB_name: the name of the data base
        """

        # create db
        self.__dbName = DB_name
        self.conn = None
        self.cursor = None
        self.conn = sqlite3.connect(self.__dbName)
        self.cursor = self.conn.cursor()

        # create tables
        self.__createTableAdmin()
        self.__createTableStation()

    def __createTableAdmin(self):
        """

        :return: creates the admins table
        """
        self.adminTbl = 'users'
        sql = f"CREATE TABLE IF NOT EXISTS {self.adminTbl}(username TEXT(16), password TEXT(16));"
        self.cursor.execute(sql)
        self.conn.commit()

    def __createTableStation(self):
        """

        :return: creates the whitelist table
        """
        self.stationTbl = 'whitelist'
        sql = f"CREATE TABLE IF NOT EXISTS {self.stationTbl}(MAC TEXT(17));"
        self.cursor.execute(sql)
        self.conn.commit()

    def checkUser(self, username, password):
        """

        :param username: username
        :param password: password
        :return: checks if the password and username match

        """
        password = hashlib.md5(password.encode()).hexdigest()
        sql = f"SELECT * FROM {self.adminTbl} WHERE username='{username}' AND password='{password}';"
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        return len(data) != 0

    def __checkUserExists(self, username):
        """

        :return: returns if the username exists
        """
        sql = f"SELECT * FROM {self.adminTbl} WHERE username='{username}';"
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        return len(data) != 0

    def checkStation(self, mac):
        """

        :param mac: mac address
        :return: if the mac exists in the whitelist
        """
        sql = f"SELECT * FROM {self.stationTbl} WHERE MAC='{mac}';"
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        return len(data) != 0

    def addUser(self, username, password):
        """

        :param username: username
        :param password: password
        :return: adds the username and the password to the admin table
        """
        # check if the username and password are between 8-16
        if (len(username) < 17) and (len(username) > 7) and (len(password) > 7) and (len(password) < 17):
            # check if the user exists
            if not (self.__checkUserExists(username)):
                # hash the password
                password = hashlib.md5(password.encode()).hexdigest()
                # inser into the admin table
                sql = f"INSERT INTO {self.adminTbl} VALUES ('{username}','{password}');"
                self.cursor.execute(sql)
                self.conn.commit()

    def addStation(self, mac):
        """

        :param mac: mac adress
        :return: adds the mac adress to the table
        """
        if len(mac) == 17:
            if not self.checkStation(mac):
                # inser into the admin table
                sql = f"INSERT INTO {self.stationTbl} VALUES ('{mac}');"
                self.cursor.execute(sql)
                self.conn.commit()

    def deleteUser(self, username):
        """

        :param username: username to delete
        :return: deletes the username and returns true or false if succeeded
        """

        flag = False
        # check if the user exists
        if self.__checkUserExists(username):
            flag = True
            # Delete the user from the table
            sql = f"DELETE FROM {self.adminTbl} WHERE username='{username}';"
            self.cursor.execute(sql)
            self.conn.commit()

        return flag

    def deleteStation(self, mac):
        """

        :param mac: mac address to delete
        :return: deletes the mac and returns true or false if succeeded
        """
        flag = False
        # check if the user exists
        if self.checkStation(mac):
            flag = True
            # Delete the user from the table
            sql = f"DELETE FROM {self.stationTbl} WHERE MAC='{mac}';"
            self.cursor.execute(sql)
            self.conn.commit()

        return flag

    def update_password(self, username, new_password):
        """

        :param username: username
        :param new_password: new password
        :return: updates the password to the username
        """
        # check if the new password is valid
        if (len(new_password) > 7) and (len(new_password) < 17):
            # check if user exists
            if self.__checkUserExists(username):
                # hash the password
                new_password = hashlib.md5(new_password.encode()).hexdigest()
                self.cursor.execute(f"UPDATE {self.adminTbl} SET password = '{new_password}' WHERE username='{username}';")
                self.conn.commit()

    def send_stations(self):
        """

        :return: sends a list with all the stations
        """

        self.cursor.execute(f"SELECT * FROM {self.stationTbl};")
        data = self.cursor.fetchall()

        stations = []
        for tup in data:
            stations.append(tup[0])
        return stations


def main():
    myDB = DB("ToriDB")
    print(myDB.send_stations())
    # station_mac = "ff:ee:dd:cc:bb:aa"
    # username = "namiko12345"
    # password = "passoword1234"
    # print("CheckUser1 - " + str(myDB.checkUser(username, password)))
    # myDB.addUser(username, password)
    # print("CheckUser2 - " + str(myDB.checkUser(username, password)))
    # myDB.update_password("namiko12345", "imashelnoamshava")
    # print(myDB.deleteUser("namiko12345"))
    # myDB.addStation(station_mac)
    # print(myDB.checkStation(station_mac))
    # print(myDB.deleteStation(station_mac))
    # print(myDB.deleteStation(station_mac))


if __name__ == "__main__":
    main()