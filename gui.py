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

        # Get host details and select first VDI to track
        self.new_host()
        # Create panel
        #self.populate_page()

        # Create menu
        menu = Menu(self.master)
        self.master.config(menu=menu)
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=self.new_vdi)

        # Create buttons
        self.button = Button(
            self.master, text="QUIT", fg="red", command=self.master.quit
        )
        self.button.pack(side=RIGHT, padx=5, pady=5)


    def get_details(self, object, type):
        """Function to get details i.e. name label for a given  object ref"""
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
        """Function to request details on host and VDI"""
        d = new_host_dialog(self.master)
        self._pool_master_address, self._username, self._password = d.result
        self._session = self.create_new_session()
        v = new_vdi_dialog(self.master)
        self._vdi, second = v.result
        print(self._vdi)
        self.find_vms()
        b = backup.Backup(self._pool_master_address, self._username, self._password, self._vm_uuid)
        print(b._get_timestamp())


    def create_new_session(self):
        """Function to create new session"""
        session = XenAPI.Session("https://" + self._pool_master_address, ignore_ssl=True)
        session.login_with_password(self._username, self._password, "0.1", "CBT example")
        return session


    def find_vms(self):
        """Temporary function to get first VM"""
        vms = self._session.xenapi.VM.get_all()
        self._vm_uuid = self._session.xenapi.VM.get_uuid(vms[0])
        print(self._vm_uuid)


    def new_vdi(self):
        """Function to request new user selected VDI"""
        v = new_vdi_dialog(self.master)
        self._vdi, second = v.result
        print(self._vdi)


    def populate_page(self):
        """Placeholder function to populate frame with data"""
        # Set up frames
        # Populate pages
        self.populate_tracked()


class new_vdi_dialog(SimpleDialog.Dialog):
    def create_new_session(self):
        session = XenAPI.Session("https://dt56.uk.xensource.com", ignore_ssl=True)
        session.login_with_password("root", "xenroot", "0.1", "CBT example")
        return session

    def body(self, master):
        self._session = self.create_new_session()
        Label(master, text="VM").grid(row=0)
        Label(master, text="VDI").grid(row=1)

        self.sr_listbox = Listbox(master)
        self.sr_listbox.grid(row=0, column=1)
        self.sr_listbox.insert(END, "Select an SR")

        VMs = self._session.xenapi.VM.get_all()
        self.VMs = []
        for VM in VMs:
            if not self._session.xenapi.VM.get_is_a_template(VM):
                print("remove")
                self.VMs.append(VM)

        for VM in self.VMs:
            self.sr_listbox.insert(END, VM)
        self.VM = None

        self.vdi_listbox = Listbox(master)
        self.vdi_listbox.grid(row=1, column=1)
        self.vdi_listbox.insert(END, "Select a VDI")

        self.poll()


    def apply(self):
        vdi = self.vdi_listbox.curselection()
        print(vdi)
        print(self.VDIs)
        print(vdi[0]-1)
        first = self.VDIs[vdi[0] - 1]
        print("Results are:")
        second = self.VMs[self.VM[0]-1]
        self.result = first, second


    def poll(self):
        now = self.sr_listbox.curselection()
        print("selected")
        print(now)
        if now != self.VM:
            print("now")
            if now:
                print("test")
                self.list_has_changed(now)
                self.VM = now
        self.after(250, self.poll)


    def list_has_changed(self, selection):
        self.vdi_listbox.delete(0,END)
        self.vdi_listbox.insert(END, "Select a VDI")

        VBDs = self._session.xenapi.VM.get_VBDs(self.VMs[selection[0]-1])
        self.VDIs = []
        for VBD in VBDs:
            self.VDIs.append(self._session.xenapi.VBD.get_VDI(VBD))
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


"""class option_dialog(SimpleDialog.Dialog):
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
                self.results.append(key)"""