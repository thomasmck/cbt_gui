from tkinter import *
from tkinter import simpledialog as SimpleDialog
import backup
import XenAPI

class App():

    def __init__(self, master):

        self.master = master
        # Create frame
        frame = Frame(self.master, relief=RAISED, borderwidth=1)
        frame.pack(fill=BOTH, expand=True)

        #Get host details
        self.new_host()
        # Create panel
        #self.populate_page()

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
        self.button.pack(side=RIGHT, padx=5, pady=5)


    def get_details(self, object, type):
        x = {"VDI": self._session.xenapi.VDI}
        print("get_details")
        details = {}
        #session_base = getattr(self._session.xenapi, type)
        #print session_base
        #y = getattr(x[type], "get_name_label(%s)" %object)
        #print y
        #details["name_label"] = y
        print(details)
        #details["uuid"] = session_base.get_uuid(object)


    def new_host(self):
        d = new_host_dialog(self.master)
        self._pool_master_address, self._username, self._password = d.result
        self._session = self.create_new_session()
        #self.gather_host_info()
        v = new_vdi_dialog(self.master)
        self._vdi = v.result
        print(self._vdi)
        self.find_vms()
        b = backup.Backup(self._pool_master_address, self._username, self._password, self._vm_uuid)
        print(b._get_timestamp())


    def create_new_session(self):
        session = XenAPI.Session("https://" + self._pool_master_address, ignore_ssl=True)
        session.login_with_password(self._username, self._password, "0.1", "CBT example")
        return session

    def find_vms(self):
        vms = self._session.xenapi.VM.get_all()
        self._vm_uuid = self._session.xenapi.VM.get_uuid(vms[0])
        print(self._vm_uuid)

    def gather_host_info(self):
        networks = self._session.xenapi.network.get_all()
        print(networks)
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
        print("tracked VDIs")
        print(self.tracked_VDIs)
        #for VDI in self.tracked_VDIs:
        #   print self.get_details(VDI, "VDI")


    def populate_page(self):
        # Set up frames
        # Populate pages
        self.populate_tracked()


    def populate_tracked(self):
        for tracked_VDI in self.tracked_VDIs:
            w = Label(self.master, text=tracked_VDI)
            w.pack(padx=5)


    def populate_stats(self):
        pass


    def populate_details(self):
        pass


class option_dialog(SimpleDialog.Dialog):
    # TODO: Make generic dialog class

    def body(self, master):
        row = 0
        self.options = options
        unique_name = ""
        for key, value in self.options.iteritems():
            #Create checkbox options for which one to track
            unique_name = value.replace(" ","")
            Label(master, text=value).grid(row=row)
            setattr(self, unique_name, Entry(master))
            y = getattr(self, unique_name)
            y.grid(row=row, column=1)
            row += 1
        print(self.options)
        return getattr(self, unique_name)  # initial focus

    def apply(self):
        self.results = []
        for key, value in self.options.iteritems():
            unique_name = value.replace(" ", "")
            y = getattr(self, unique_name)
            if y.get():
                self.results.append(key)


class new_vdi_dialog(SimpleDialog.Dialog):
    def create_new_session(self):
        session = XenAPI.Session("https://dt56.uk.xensource.com", ignore_ssl=True)
        session.login_with_password("root", "xenroot", "0.1", "CBT example")
        return session

    def body(self, master):
        self._session = self.create_new_session()
        Label(master, text="SR").grid(row=0)
        Label(master, text="VDI").grid(row=1)

        self.sr_listbox = Listbox(master)
        self.sr_listbox.grid(row=0, column=1)
        self.sr_listbox.insert(END, "Select an SR")

        self.SRs = self._session.xenapi.SR.get_all()
        for SR in self.SRs:
            self.sr_listbox.insert(END, SR)
        self.SR = None

        self.vdi_listbox = Listbox(master)
        self.vdi_listbox.grid(row=1, column=1)
        self.vdi_listbox.insert(END, "Select a VDI")

        VDIs = []
        if self.SR:
            VDIs = self._session.xenapi.SR.get_VDIs(self.SR)
        for VDI in VDIs:
            self.vdi_listbox.insert(END, VDI)

        self.poll()


    def apply(self):
        vdi = self.vdi_listbox.curselection()
        print(vdi)
        print(self.VDIs)
        print(vdi[0]-1)
        first = self.VDIs[vdi[0] - 1]
        self.result = first


    def poll(self):
        now = self.sr_listbox.curselection()
        print("selected")
        print(now)
        if now != self.SR:
            if now:
                print("test")
                self.list_has_changed(now)
            self.current = now
        self.after(250, self.poll)

    def list_has_changed(self, selection):
        self.vdi_listbox.delete(0,END)
        self.vdi_listbox.insert(END, "Select a VDI")

        self.VDIs = self._session.xenapi.SR.get_VDIs(self.SRs[selection[0]-1])
        for VDI in self.VDIs:
            self.vdi_listbox.insert(END, VDI)


class new_host_dialog(SimpleDialog.Dialog):
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
    root.geometry("800x600+300+300")
    app = App(root)
    root.mainloop()
    root.destroy()

if __name__ == "__main__":
    main()