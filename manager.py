import wx
import queue
import RSAClass
import ManagerProtocol
import AESClass
import StationComs
import pubsub.pub as pub


def exchange_keys(manager_client_q, manager_client):
    """

    :param manager_client: the StationComs of the manager client
    :return: exchanges keys
    """
    global public_key, rsa_keys
    msg = ManagerProtocol.buildPublishPKeyMA(public_key.decode())
    print(msg)
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
    def __init__(self, parent=None):
        #super(mainFrame, self).__init__(parent, title="Tori", size=(wx.DisplaySize()))
        wx.Frame.__init__(self, None,title="Tori", size=(wx.DisplaySize()))
        # create status bar
        self.CreateStatusBar(1)

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
        wx.Panel.__init__(self, parent)

        self.frame = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        v_box = wx.BoxSizer()

        # all panels
        self.login = LoginPanel(self, self.frame)
        self.main_menu = MainMenuPanel(self, self.frame)
        self.change_station = ChangeNumStationPanel(self, self.frame)

        v_box.Add(self.login)
        v_box.Add(self.main_menu)
        v_box.Add(self.change_station)

        self.login.Show()

        self.SetSizer(v_box)
        self.Layout()


class LoginPanel(wx.Panel):

    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition,
                          size=(wx.DisplaySize()),
                          style=wx.SIMPLE_BORDER)

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

        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def handle_login(self, event):
        global public_key, first_login, sym_key, manager_client, manager_client_q
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
            # create client
            if first_login:
                manager_client_q = queue.Queue()
                manager_client = StationComs.StationComs(2028, "127.0.0.1", manager_client_q)
                # exchange keys
                sym_key = exchange_keys(manager_client_q, manager_client)

            # send username and password
            msg = ManagerProtocol.buildSendUserAndPassword(username, password)
            enc_msg = sym_key.encrypt(msg)
            manager_client.sendMsg(enc_msg)
            Correct = isLoginCorrect(manager_client_q, sym_key)
            # login successfully
            if str(Correct) == "True":
                # move to menu screen
                self.frame.SetStatusText("")
                self.Hide()
                self.parent.main_menu.Show()

                # get the list of all the stations and the number of stations per msg
                # wait for response
                data = manager_client_q.get()
                # decrypt rsa response from server
                data = sym_key.decrypt(data)
                code, msg = ManagerProtocol.unpack(data)
                # code will be '10'

                # msg[0] = num of stations per msg
                pub.sendMessage("current_changer", msg[0])


            else:
                wx.MessageBox("Wrong Username or Password", "Response", wx.OK)
                first_login = False


class MainMenuPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition,
                          size=(wx.DisplaySize()),
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
        size = (300, 150))

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

    def change_num_stations(self, event):
        """
        the function of the ChangeNumStation button
        :return: Shows the "Change Num of Station per message" screen
        """
        self.Hide()
        self.parent.change_station.Show()


class ChangeNumStationPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition,
                          size=(wx.DisplaySize()),
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

        currentNum_box.Add(self.currentNum_Text)

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

        # # button for knowing how many stations per msg currently
        # askBtn = wx.Button(self, wx.ID_ANY, label="Current number?",  size=(200, 60))
        # # bind the button
        # askBtn.Bind(wx.EVT_BUTTON, self.handle_ask)

        changeBox.Add(changeBtn, 0, wx.ALL, 5)
        # changeBox.Add(askBtn, 0, wx.ALL, 5)

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

    def handle_ask(self, event):
        global sym_key, manager_client, manager_client_q
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
        self.Hide()
        self.parent.main_menu.Show()


if __name__ == '__main__':
    rsa_keys = RSAClass.RSAClass()
    public_key = rsa_keys.get_public_key_pem()
    first_login = True
    app = wx.App(False)
    first_Frame = mainFrame()
    app.MainLoop()