from Tkinter import *
import tkSimpleDialog
import cbt_tests
import XenAPI

class App():

    def __init__(self, master):

        self.master = master
        # Create frame
        frame = Frame(self.master)
        frame.pack()

        # Create panel
        Label(master, text="Thakyou for using CBT backup").pack()
        Label(master, text="Please connect to a new host").pack()

        # Create menu
        menu = Menu(self.master)
        master.config(menu=menu)
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=self.new_host)

        # Create buttons
        self.button = Button(
            master, text="QUIT", fg="red", command=master.quit
        )
        self.button.pack(side=LEFT)


    def get_details(self, object, type):
        x = {"VDI": self._session.xenapi.VDI}
        print "get_details"
        details = {}
        #session_base = getattr(self._session.xenapi, type)
        #print session_base
        y = getattr(x[type], "get_name_label(%s)" %object)
        print y
        details["name_label"] = y
        print details
        #details["uuid"] = session_base.get_uuid(object)


    def new_host(self):
        d = new_host_dialog(self.master)
        self._pool_master_address, self._username, self._password = d.result
        self._session = self.create_new_session()
        self.gather_host_info()


    def create_new_session(self):
        session = XenAPI.Session("https://" + self._pool_master_address, ignore_ssl=True)
        session.login_with_password(self._username, self._password, "0.1", "CBT example")
        return session

    def gather_host_info(self):
        networks = self._session.xenapi.network.get_all()
        print networks
        # User selects which networks to use
        # User selects which SR they are interested in
        SRs = self._session.xenapi.SR.get_all()
        global options
        options = {}
        for SR in SRs:
            name_label = self._session.xenapi.SR.get_name_label(SR)
            options[SR] = name_label
        selected_SRs = option_dialog(self.master)
        self.SR_dict = selected_SRs.results
        # Find the VDIs for the selected SRs
        VDIs = []
        for SR in self.SR_dict:
            VDI_list = self._session.xenapi.SR.get_VDIs(SR)
            for VDI in VDI_list:
                VDIs.append(VDI)
        options = {}
        # User selects which VDI to track
        for VDI in VDIs:
            name_label = self._session.xenapi.VDI.get_name_label(VDI)
            options[VDI] = name_label
        selected_VDIs = option_dialog(self.master)
        self.tracked_VDIs = selected_VDIs.results
        print self.tracked_VDIs
        for VDI in self.tracked_VDIs:
            print self.get_details(VDI, "VDI")

    def populate_page(self):
        


class option_dialog(tkSimpleDialog.Dialog):
    # TODO: Make generic dialog class

    def body(self, master):
        row = 0
        self.options = options
        for key, value in self.options.iteritems():
            #Create checkbox options for which one to track
            Label(master, text=value).grid(row=row)
            row += 1
        print self.options

        self.rand_string ="abcdefghijk"
        for x in range(0, len(self.options)):
            setattr(self, self.rand_string[x], Entry(master))
            y = getattr(self, self.rand_string[x])
            y.grid(row=x, column=1)
        return getattr(self, "a")  # initial focus

    def apply(self):
        self.results = []
        x = 0
        for key, value in self.options.iteritems():
            y = getattr(self, self.rand_string[x])
            if y.get():
                self.results.append(key)
            x += 1


class new_host_dialog(tkSimpleDialog.Dialog):
    # TODO: Make generic dialog class

    def body(self, master):
        Label(master, text="IP address:").grid(row=0)
        Label(master, text="Username:").grid(row=1)
        # TODO: Mask password
        Label(master, text="Password:").grid(row=2)

        self.e1 = Entry(master)
        self.e2 = Entry(master)
        self.e3 = Entry(master)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        return self.e1  # initial focus

    def apply(self):
        first = self.e1.get()
        second = self.e2.get()
        third = self.e3.get()
        self.result = first, second, third  # or something


def main():
    root = Tk()
    app = App(root)
    root.mainloop()
    root.destroy()

if __name__ == "__main__":
    main()