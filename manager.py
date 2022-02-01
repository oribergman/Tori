import wx
import queue
import os
import threading
import RSAClass
import ManagerProtocol
import AESClass
import StationComs
try:
    import pubsub.pub as pub
except:
    os.system("pip install pypubsub")
    import pubsub.pub as pub


def exchange_keys(manager_client_q, manager_client, rsa_keys):
    """

    :param manager_client: the StationComs of the manager client
    :return: exchanges keys
    """
    public_key = rsa_keys.get_public_key_pem()
    msg = ManagerProtocol.buildPublishPKeyMA(public_key.decode())
    manager_client.sendMsg(msg)

    # wait for response
    data = manager_client_q.get()
    # decrypt rsa response from server
    data = rsa_keys.decrypt_msg(data).decode()
    code, msg = ManagerProtocol.unpack(data)

    # the code will always be '3' - server sent the sym_key
    sym_key = AESClass.AESCipher(msg)

    return sym_key


def isLoginCorrect(manager_client_q, sym_key):
    """

    :param manager_client_q: the queue of the client's msgs
    :return: the server's answer about the login
    """

    data = manager_client_q.get()
    data = sym_key.decrypt(data)
    code, msg = ManagerProtocol.unpack(data)

    # code will be '9' for sure
    return msg


def macValid(mac):
    """

    :param mac: mac address
    :return: checks if the mac is valid
    """
    valid = False
    if type(mac) == str:
        mac_list = mac.split(":")
        if len(mac_list) == 6:
            valid = True
            for pair in mac_list:
                if not valid:
                    break
                if len(pair) != 2:
                    valid = False
                else:
                    # all characters between are a digit or a letter
                    if not (pair[0].isalpha() or pair[0].isdigit()):
                        valid = False
                    elif not (pair[1].isalpha() or pair[1].isdigit()):
                        valid = False
    return valid


class mainFrame(wx.Frame):
    def __init__(self, sym_key, manager_client, parent=None):
        super(mainFrame, self).__init__(parent, title="Tori", size=(1000,800) ,style = wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER)
        # create status bar
        self.CreateStatusBar(1)

        self.sym_key = sym_key
        self.com = manager_client

        main_panel = MainPanel(self)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(main_panel, 1, wx.EXPAND)
        # adding icon
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("ToriLogo.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.SetSizer(box)
        self.Layout()
        self.Show()


class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,size=(1000,800))

        self.frame = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        v_box = wx.BoxSizer()

        # all panels
        self.login = LoginPanel(self, self.frame)
        self.main_menu = MainMenuPanel(self, self.frame)
        self.change_station = ChangeNumStationPanel(self, self.frame)
        self.stations = StationsPanel(self, self.frame)

        v_box.Add(self.login,0,wx.EXPAND,0)
        v_box.Add(self.main_menu,0,wx.EXPAND,0)
        v_box.Add(self.change_station,0,wx.EXPAND,0)
        v_box.Add(self.stations,0,wx.EXPAND,0)

        self.login.Show()

        self.SetSizer(v_box)
        self.Layout()


class LoginPanel(wx.Panel):

    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition,
                          size=(1000,800), style=wx.SIMPLE_BORDER)

        self.frame = frame
        self.parent = parent

        self.SetBackgroundColour(wx.LIGHT_GREY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # title
        title_image_box = wx.BoxSizer(wx.HORIZONTAL)

        # adding the logo picture
        logo_bmp = wx.Image("ToriLogo.png", wx.BITMAP_TYPE_ANY)
        logo_bmp.Rescale(600, 300)

        Image = wx.StaticBitmap(self, bitmap=wx.Bitmap(600, 300))
        Image.SetBitmap(wx.Bitmap(logo_bmp))

        title_image_box.Add(Image, 0, wx.ALIGN_CENTER, 5)

        # username
        username_box = wx.BoxSizer(wx.HORIZONTAL)
        name_text = wx.StaticText(self, 1, label="Username: ")
        self.userField = wx.TextCtrl(self, -1, name="Enter name",
                                    size=(150, -1))
        username_box.Add(name_text, 0, wx.ALL, 5)
        username_box.Add(self.userField, 0, wx.ALL, 5)

        # password
        passBox = wx.BoxSizer(wx.HORIZONTAL)
        passText = wx.StaticText(self, 1, label="Password: ")

        self.passField = wx.TextCtrl(self, -1, name="password", style=wx.TE_PASSWORD,
                        size = (150, -1))

        passBox.Add(passText, 0, wx.ALL, 5)
        passBox.Add(self.passField, 0, wx.ALL, 5)

        # login button
        btnBox = wx.BoxSizer(wx.HORIZONTAL)
        loginBtn = wx.Button(self, wx.ID_ANY, label="Login",
        size = (200, 60))
        loginBtn.Bind(wx.EVT_BUTTON, self.handle_login)
        btnBox.Add(loginBtn, 0, wx.ALL, 5)

        # add all elements to sizer
        sizer.Add(title_image_box, 0, wx.CENTER|wx.ALL, 5)
        sizer.AddSpacer(50)
        sizer.Add(username_box, 0, wx.CENTER | wx.ALL, 5)
        sizer.Add(passBox, -1, wx.CENTER | wx.ALL, 5)
        sizer.AddSpacer(30)
        sizer.Add(btnBox, wx.CENTER | wx.ALL, 5)


        pub.subscribe(self.handle_login_ans, 'login_ans')

        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def handle_login_ans(self, status):
        if status == False:
            wx.MessageBox("Wrong Username or Password", "Response", wx.OK)
        else:
            print("ok")
            # login successfully

            # move to menu screen
            self.frame.SetStatusText("")
            self.Hide()
            self.parent.main_menu.Show()

    def handle_login(self, event):
        # extract username and password
        username = self.userField.GetValue()
        password = self.passField.GetValue()

        # username not entered
        if not username:
            wx.MessageBox("No username entered", "Error", wx.OK)
        # password not entered
        elif not password:
            wx.MessageBox("No password entered", "Error", wx.OK)

        # checking with server if user and password correct
        else:
            self.frame.SetStatusText("Checking with server...")

            # send username and password
            msg = ManagerProtocol.buildSendUserAndPassword(username, password)
            enc_msg = self.frame.sym_key.encrypt(msg)
            self.frame.com.sendMsg(enc_msg)
            # Correct = isLoginCorrect(manager_client_q, sym_key)
            # # login successfully
            # if str(Correct) == "True":
            #     # move to menu screen
            #     self.frame.SetStatusText("")
            #     self.Hide()
            #     self.parent.main_menu.Show()
            #
            #     # get the list of all the stations and the number of stations per msg
            #     # wait for response
            #     data = manager_client_q.get()
            #     # decrypt rsa response from server
            #     data = sym_key.decrypt(data)
            #     code, msg = ManagerProtocol.unpack(data)
            #     # code will be '10'
            #     stations_per_msg = msg[0]
            #     stations = msg[1]
            #
            #     # send through pubsub
            #     wx.CallAfter(pub.sendMessage, "current_changer", currentNum=stations_per_msg)
            #     wx.CallAfter(pub.sendMessage, "fill_list", stations=stations)
            #
            # else:
            #     wx.MessageBox("Wrong Username or Password", "Response", wx.OK)



class MainMenuPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition,
                          size=(1000,800),
                          style=wx.SIMPLE_BORDER)

        self.frame = frame
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # add image logo title
        title_image_box = wx.BoxSizer(wx.HORIZONTAL)

        # adding the logo picture
        logo_bmp = wx.Image("ToriLogo.png", wx.BITMAP_TYPE_ANY)
        logo_bmp.Rescale(600, 300)

        Image = wx.StaticBitmap(self, bitmap=wx.Bitmap(600, 300))
        Image.SetBitmap(wx.Bitmap(logo_bmp))

        title_image_box.Add(Image, 0, wx.ALIGN_CENTER, 5)

        # box for option buttons
        optionsBox1 = wx.BoxSizer(wx.HORIZONTAL)
        # button of add station
        stationButton = wx.Button(self, wx.ID_ANY, label="Stations",
        size=(300, 150))

        # bind the button
        stationButton.Bind(wx.EVT_BUTTON, self.station_info_btn)

        # button of change the number of stations per msg
        changeNumButton = wx.Button(self, wx.ID_ANY, label= """Change Num of
        Stations per msg""",
        size=(300, 150))

        # bind the button
        changeNumButton.Bind(wx.EVT_BUTTON, self.change_num_stations)

        # creating font
        font = wx.Font(24, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        stationButton.SetFont(font)
        changeNumButton.SetFont(font)

        # adding buttons to the box
        optionsBox1.Add(stationButton, 1, wx.LEFT, 5)
        optionsBox1.Add(changeNumButton, 1, wx.CENTER, 5)

        # bind all buttons

        # adding sizers
        sizer.Add(title_image_box, 0, wx.CENTER, 5)
        sizer.AddSpacer(100)
        sizer.Add(optionsBox1, 0, wx.CENTER, 5)

        self.SetSizer(sizer)
        self.Layout()
        self.Hide()

    def station_info_btn(self, event):
        self.Hide()
        self.parent.stations.Show()

    def change_num_stations(self, event):
        """
        the function of the ChangeNumStation button
        :return: Shows the "Change Num of Station per message" screen
        """
        self.Hide()
        self.parent.change_station.Show()


class StationsPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1000,800),

        style=wx.SIMPLE_BORDER)

        self.frame = frame
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # add back button
        back_box = wx.BoxSizer(wx.HORIZONTAL)

        # create img
        backImg = wx.Image("back.png", wx.BITMAP_TYPE_ANY)
        backImg.Rescale(100, 100)
        # create bmp
        backBmp = wx.Bitmap(backImg)
        backBtn = wx.BitmapButton(self, wx.ID_ANY, bitmap=backBmp, size=wx.DefaultSize)
        # set color of button
        backBtn.SetBackgroundColour(wx.LIGHT_GREY)
        # remove outline
        backBtn.SetWindowStyleFlag(wx.NO_BORDER)
        # bind the button
        backBtn.Bind(wx.EVT_BUTTON, self.handle_back)

        back_box.Add(backBtn, 0, wx.ALIGN_LEFT, 5)

        # add image logo title
        title_image_box = wx.BoxSizer(wx.HORIZONTAL)

        # adding the logo picture
        logo_bmp = wx.Image("ToriLogo.png", wx.BITMAP_TYPE_ANY)
        logo_bmp.Rescale(400, 200)

        Image = wx.StaticBitmap(self, bitmap=wx.Bitmap(400, 200))
        Image.SetBitmap(wx.Bitmap(logo_bmp))

        title_image_box.Add(Image, 0, wx.ALIGN_CENTER, 5)

        # creating the small panel
        self.smallPanel = wx.Panel(self, size=(400, 400), style = wx.SIMPLE_BORDER)

        # sizer for small panel
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.listbox = wx.ListBox(self.smallPanel)
        # subscribe with pub sub to fill the list
        pub.subscribe(self.fill_list, "fill_list")

        # title box
        title_box = wx.BoxSizer(wx.HORIZONTAL)

        title_Text = wx.StaticText(self.smallPanel, 0, label="Stations MAC list:")
        # creating font
        font = wx.Font(9, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        title_Text.SetFont(font)

        title_box.Add(title_Text, 0, wx.LEFT, 5)

        # creating the button panel
        btnPanel = wx.Panel(self.smallPanel)
        vbox = wx.BoxSizer(wx.VERTICAL)
        addBtn = wx.Button(btnPanel, wx.ID_ANY, 'Add', size=(90, 30))
        delBtn = wx.Button(btnPanel, wx.ID_ANY, 'Delete', size=(90, 30))

        self.Bind(wx.EVT_BUTTON, self.NewStation, id=addBtn.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnDelete, id=delBtn.GetId())

        vbox.Add((-1, 20))
        vbox.Add(addBtn)
        vbox.Add(delBtn, 0, wx.TOP, 5)
        btnPanel.SetSizer(vbox)

        hbox.Add(title_box, 0, wx.LEFT, 5)
        hbox.AddSpacer(10)
        hbox.Add(self.listbox, wx.ID_ANY, wx.EXPAND | wx.ALL, 20)
        hbox.Add(btnPanel, 0.6, wx.EXPAND | wx.RIGHT, 20)

        self.smallPanel.Centre()
        self.smallPanel.SetSizer(hbox)
        self.smallPanel.Layout()

        mainSizer.Add(back_box, 0, wx.LEFT, 5)
        mainSizer.Add(title_image_box, 0, wx.CENTER|wx.TOP, 5)
        mainSizer.AddSpacer(10)
        mainSizer.Add(self.smallPanel, 0, wx.CENTER,5)

        self.SetSizer(mainSizer)
        self.Layout()
        self.Hide()

    def NewStation(self, event):
        """
        triggers when the add button is pressed
        :return: add a new station
        """
        mac = wx.GetTextFromUser('Enter a MAC', 'Insert MAC')

        # if the mac is valid and there are no duplicates
        if macValid(mac):
            if mac not in self.listbox.GetStrings():
                # append to list
                self.listbox.Append(mac)
                # tell the server to add the station
                msg = ManagerProtocol.buildAddStationMsg(mac)
                enc_msg = self.frame.sym_key.encrypt(msg)
                self.frame.com.sendMsg(enc_msg)
            else:
                wx.MessageBox("MAC already in list", "Error", wx.OK)
        else:
            wx.MessageBox("MAC address invalid", "Error", wx.OK)

    def OnDelete(self, event):
        """
        triggers when delete in pressed
        :return: deletes the chosen station
        """
        index = self.listbox.GetSelection()
        if index != -1:
            mac = self.listbox.GetString(index)
            # deleting mac from table
            self.listbox.Delete(index)
            # telling server to delete mac
            msg = ManagerProtocol.buildDeleteStationMsg(mac)
            enc_msg = self.frame.sym_key.encrypt(msg)
            self.frame.com.sendMsg(enc_msg)

        else:
            wx.MessageBox("No MAC chosen", "Error", wx.OK)

    def fill_list(self, stations):
        """

        :param stations: list of mac addresses of the stations
        :return: fills the list
        """
        # add all the stations to list
        for mac in stations:
            self.listbox.Append(mac)

        #if not self.Hide():
        self.Layout()



    def handle_back(self, event):
        """
        triggers when the back button is pressed
        :return: goes back to main menu
        """
        self.frame.SetSize((1000, 800))
        self.Hide()
        self.parent.main_menu.Show()


class ChangeNumStationPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition,
                          size=(1000,800),
                          style=wx.SIMPLE_BORDER)

        self.frame = frame
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # add back button
        back_box = wx.BoxSizer(wx.HORIZONTAL)

        # create img
        backImg = wx.Image("back.png", wx.BITMAP_TYPE_ANY)
        backImg.Rescale(100, 100)
        # create bmp
        backBmp = wx.Bitmap(backImg)
        backBtn = wx.BitmapButton(self, wx.ID_ANY, bitmap=backBmp, size=wx.DefaultSize)

        # set color of button
        backBtn.SetBackgroundColour(wx.LIGHT_GREY)
        # remove outline
        backBtn.SetWindowStyleFlag(wx.NO_BORDER)

        # bind the button
        backBtn.Bind(wx.EVT_BUTTON, self.handle_back)

        # add to box
        back_box.Add(backBtn, 0, wx.LEFT, 5)

        # add image logo title
        title_image_box = wx.BoxSizer(wx.HORIZONTAL)

        # adding the logo picture
        logo_bmp = wx.Image("ToriLogo.png", wx.BITMAP_TYPE_ANY)
        logo_bmp.Rescale(600, 300)

        Image = wx.StaticBitmap(self, bitmap=wx.Bitmap(600, 300))
        Image.SetBitmap(wx.Bitmap(logo_bmp))

        title_image_box.Add(Image, 0, wx.ALIGN_CENTER, 5)

        # current num box
        currentNum_box = wx.BoxSizer(wx.HORIZONTAL)

        self.currentNum_Text = wx.StaticText(self, 1, label="")

        currentNum_box.Add(self.currentNum_Text, 0, wx.CENTER, 5)

        # subscribe to pubsub to know current num of station per message
        pub.subscribe(self.change_current, "current_changer")

        # box of add station
        change_box = wx.BoxSizer(wx.HORIZONTAL)

        # textControl
        numOfStationText = wx.StaticText(self, 1, label="Change to: ")
        self.numField = wx.TextCtrl(self, -1, name="Enter a number",
                                     size=(150, -1))

        change_box.Add(numOfStationText, 0, wx.ALL, 5)
        change_box.Add(self.numField, 0, wx.ALL, 5)

        # change button
        changeBox = wx.BoxSizer(wx.HORIZONTAL)

        changeBtn = wx.Button(self, wx.ID_ANY, label="Change Number", size=(200, 60))
        # bind the button
        changeBtn.Bind(wx.EVT_BUTTON, self.handle_change)

        changeBox.Add(changeBtn, 0, wx.ALL, 5)

        # add all to sizer
        sizer.Add(back_box, 0, wx.LEFT, 5)
        sizer.Add(title_image_box, 0, wx.CENTER, 5)
        sizer.AddSpacer(50)
        sizer.Add(currentNum_box,0, wx.CENTER, 5)
        sizer.AddSpacer(15)
        sizer.Add(change_box, 0, wx.CENTER, 5)
        sizer.AddSpacer(30)
        sizer.Add(changeBox, 0, wx.CENTER, 5)

        self.SetSizer(sizer)
        self.Layout()
        self.Hide()

    def handle_change(self, event):
        global sym_key, manager_client, manager_client_q

        new_num = self.numField.GetValue()

        # checking if mac address is valid
        if new_num.isdigit():
            if (int(new_num) < 10) and (int(new_num) > 2):
                # build the msg as the protocol says
                msg = ManagerProtocol.buildChNumOfStations(new_num)
                # encrypt the msg
                enc_msg = sym_key.encrypt(msg)
                # send the msg
                manager_client.sendMsg(enc_msg)
                # add a msg box
                wx.MessageBox("Changed Successfully", "Response", wx.OK)

                # change the text of current number
                self.change_current(new_num)
            else:
                wx.MessageBox("The number must be between 3 to 9", "Error", wx.OK)
        else:
            wx.MessageBox("Please enter a number", "Error", wx.OK)

    def change_current(self, currentNum):
        """

        :param currentNum: current number of station per message
        :return: changes the label according to the number
        """

        self.currentNum_Text.SetLabel("Current number of station per message: " + currentNum)
        self.Layout()

    def handle_ask(self, event):
        """
        triggers when the "Current number?" button is clicked 
        :return: asks the server for the Current number of station per msg and presents it
        """
        # create the msg
        msg = ManagerProtocol.buildAskForNumOfStations()
        enc_msg = sym_key.encrypt(msg)

        # send the msg
        manager_client.sendMsg(enc_msg)

        # wait for response
        data = manager_client_q.get()
        data = sym_key.decrypt(data)
        code, msg = ManagerProtocol.unpack(data)

        # code will be '15' for sure
        num_of_stations = msg

        wx.MessageBox("Currently there are " + num_of_stations + " per message", "Response", wx.OK)

    def handle_back(self, event):
        """
       triggers when the back button is pressed
       :return: goes back to main menu
       """
        self.Hide()
        self.parent.main_menu.Show()


def manager_logic(recv_q, sym_key):
    while True:
        data = recv_q.get()
        data = sym_key.decrypt(data)
        code, msg = ManagerProtocol.unpack(data)
        if code == '9':
            wx.CallAfter(pub.sendMessage, "login_ans", status=msg)

        elif code == '10':
            # code will be '10'
            stations_per_msg = msg[0]
            stations = msg[1]
            # send through pubsub
            wx.CallAfter(pub.sendMessage, "current_changer", currentNum=stations_per_msg)
            wx.CallAfter(pub.sendMessage, "fill_list", stations=stations)


if __name__ == '__main__':
    rsa_keys = RSAClass.RSAClass()
    manager_client_q = queue.Queue()
    manager_client = StationComs.StationComs(2028, "127.0.0.1", manager_client_q)
    # exchange keys
    sym_key = exchange_keys(manager_client_q, manager_client, rsa_keys)
    threading.Thread(target=manager_logic, args=(manager_client_q, sym_key, )).start()

    public_key = rsa_keys.get_public_key_pem()
    first_login = True
    app = wx.App()
    first_Frame = mainFrame(sym_key= sym_key, manager_client= manager_client)
    app.MainLoop()