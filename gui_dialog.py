from tkinter import *
from tkinter import simpledialog as SimpleDialog
import XenAPI
from connections import DbConnection, XAPI

class new_vm_dialog(SimpleDialog.Dialog):
    """Dialog for selecting new VM/VDI"""

    def __init__(self, master, host):
        self.host = host
        super().__init__(master)

    def create_new_session(self):
        #TO-DO: find way to pass variables to this
        session = XenAPI.Session("https://" + self.host, ignore_ssl=True)
        session.login_with_password("root", "xenroot", "0.1", "CBT example")
        return session

    def body(self, master):
        self._session = self.create_new_session()
        Label(master, text="VM").grid(row=0)

        self.vm_listbox = Listbox(master)
        self.vm_listbox.grid(row=0, column=1)
        self.vm_listbox.insert(END, "Select a VM")

        self.VMs = [vm for vm in self._session.xenapi.VM.get_all() if not self._session.xenapi.VM.get_is_a_template(vm)]

        for VM in self.VMs:
            VM_name_label = self._session.xenapi.VM.get_name_label(VM)
            self.vm_listbox.insert(END, VM_name_label)
        self.VM = None

    def apply(self):
        vm = self.vm_listbox.curselection()
        print("VM")
        print(vm)
        vm_uuid =  self._session.xenapi.VM.get_uuid(self.VMs[vm[0]-1])
        self.result = vm_uuid


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