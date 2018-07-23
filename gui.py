from tkinter import *
from tkinter import simpledialog as SimpleDialog
import backup as BackUp
from xs_objects import *
from connections import XAPI
import XenAPI
import matplotlib
import numpy
import time
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import sqlite3
import threading
from gui_dialog import new_vm_dialog, new_host_dialog


class App():

    def __init__(self, master, session):

        self.master = master
        self.setup()
        self.__vdi = []
        self.__vms = []
        self.prexisting = False

        # TODO: Move this stuff into a function
        # Create menu bar
        menu = Menu(self.master)
        self.master.config(menu=menu)
        filemenu = Menu(menu)
        
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New host", command=self.new_host)
        filemenu.add_command(label="New VM", command=self.new_vm)
        filemenu.add_command(label="Backup", command=self.backup_vm)
        filemenu.add_command(label="Exit", command=quit)

        # If we have existing settings then gather them
        # TODO: If we have an error when connecting the first time we get stuck in loop till db is deleted
        # TODO: Create class to manage database connections

        # Just work with one host for now
        self.__local = Local()
        # Check if there are existing hosts in the database
        if self.__local.pre_existing:
            self.__host = self.__local.hosts[0]
            self.__vms = self.__host.vms
        # self._session = session
        self.populate_page()

    def get_existing_details(self):
        self.c.execute("SELECT vm_uuid FROM vms")
        vms = self.c.fetchall()
        for vm in vms:
            self._vm_uuid.append(vm[0])
        # TODO: Create class/function to handle db calls
        self.c.execute("SELECT host, username, password FROM hosts")
        host_details = self.c.fetchall()
        self._pool_master_address = host_details[0][0]
        self._username = host_details[0][1]
        self._password = host_details[0][2]

    def setup(self):
        """Create basic frame structure"""
        self.m1 = PanedWindow(self.master, bg='black')
        self.m1.pack(fill=BOTH, expand=1)

        self.left_frame = Frame(self.master, bg='white')
        self.m1.add(self.left_frame)

        self.m2 = PanedWindow(self.m1, orient=VERTICAL, bg='black')
        self.m1.add(self.m2)

        self.top_frame = Frame(self.master, bg='white')
        self.m2.add(self.top_frame)

        self.bottom_frame = Frame(self.master, bg='white')
        self.m2.add(self.bottom_frame)

        Label(self.left_frame, text="VM", width=30).grid(row=0, sticky='W')
        Label(self.top_frame, text="Graphs", width=100).grid(row=0, sticky='W')
        Label(self.bottom_frame, text="Details", width=100).grid(row=0, sticky='W')

    def new_host(self):
        """Function to request details on host and create session with host"""
        d = new_host_dialog(self.master)
        address, username, password = d.result
        self.__host = Host(address, username, password, self.__local.db)
        self.__vms = self.__host.vms
        print("VMS: %s" % self.__vms)
        self.populate_page()

    def new_vdis(self, vm_uuid):
        print("VM uuid: %s" % vm_uuid)
        vm_ref = self._session.xenapi.VM.get_by_uuid(vm_uuid)
        vbd_refs = self._session.xenapi.VM.get_VBDs(vm_ref)
        print("VBD refs: %s" % vbd_refs)
        # (vdi_id integer primary key, vdi_uuid text, vdi_name text, record text, vm_id, FOREIGN KEY(vm_id) REFERENCES vms(vm_id))''')
        for vbd_ref in vbd_refs:
            vdi_ref = self._session.xenapi.VBD.get_VDI(vbd_ref)
            if vdi_ref == "OpaqueRef:NULL":
                continue
            vdi_name_label = self._session.xenapi.VDI.get_name_label(vdi_ref)
            print(vdi_name_label)
            vdi_uuid = self._session.xenapi.VDI.get_uuid(vdi_ref)
            print(vdi_uuid)
            vdi_record = str(self._session.xenapi.VDI.get_record(vdi_ref))
            print(vdi_record)
            self.c.execute("SELECT vm_id FROM vms WHERE vm_uuid=(?)", (vm_uuid,))
            vm_id = int(self.c.fetchall()[0][0])
            print("VM id: %s" % vm_id)
            self.c.execute("INSERT INTO vdis(vdi_uuid, vdi_name, record, vm_id) VALUES (?,?,?,?)",
                           (vdi_uuid, vdi_name_label, vdi_record, vm_id))
            self.conn.commit()

    def new_vm(self):
        """Launch dialog to get vm/vdi. Populate page with details"""
        v = new_vm_dialog(self.master, self._pool_master_address)
        vm_uuid = v.result
        # TODO: should get rid of self._vm_uuid entirely
        if vm_uuid not in self._vm_uuid:
            self._vm_uuid.append(vm_uuid)
            ref = self._session.xenapi.VM.get_by_uuid(vm_uuid)
            name_label = self._session.xenapi.VM.get_name_label(ref)
            record_string = str(self._session.xenapi.VM.get_record(ref))
            # (vm_id integer primary key, vm_uuid text, vm_name text, record text, tracked bool)
            self.c.execute("INSERT INTO vms(vm_uuid, vm_name, record, tracked) VALUES (?,?,?,?)",
                           (vm_uuid, name_label, record_string, "True"))
            self.conn.commit()
            self.new_vdis(vm_uuid)
        # TEMP
        self.populate_page()

    def backup_vm(self):
        # Backup a VM
        now = self.vm_list.curselection()
        vm = self._vm_uuid[now[0]]
        self.c.execute("SELECT date('now')")
        timestamp = self.c.fetchall()[0][0]
        self.c.execute("INSERT INTO backups VALUES (?,?)", (timestamp, vm))
        self.conn.commit()
        #def backup(master, vm, pwd, uname='root', tls=True):
        self.backup = BackUp.backup(self._pool_master_address, vm, self._password, tls=False)
        # Make a background task otherwise gui cannot be used
        location = self.backup.backup()
        self.graph_populate()


    def create_new_session(self):
        """Function to create new session"""
        session = XenAPI.Session("https://" + self._pool_master_address, ignore_ssl=True)
        session.login_with_password(self._username, self._password, "0.1", "CBT example")
        return session

    def graph_populate(self):
        """Generate graph of how many backups have been done each day"""
        try:
            self.canvas.get_tk_widget().destroy()
        except Exception as e:
            print(e)
            pass
        print("THERE")
        # Add 0 entries for empty days
        self.c.execute("SELECT date, count(date) FROM backups WHERE date BETWEEN datetime('now', '-6 days') AND datetime('now', 'localtime') GROUP BY date ORDER BY date ASC")
        data = self.c.fetchall()
        x = []
        y = []
        for d in data:
            print(time.strftime("%Y-%m-%d"))
            x.append(d[0])
            y.append(int(d[1]))

        ind = numpy.array(x)
        width = .5

        # Need to add axis titles and sort out date overlap
        f = Figure(figsize=(5, 2), dpi=100)
        a = f.add_subplot(111)

        rects1 = a.bar(ind, y, width)

        a.set_title('Backup Frequency')
        a.set_xlabel('Date')
        a.set_ylabel('Number of Backups')

        self.canvas = FigureCanvasTkAgg(f, master=self.top_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().grid()
        print("HERE")

    def populate_page(self):
        """Function to populate left frame with tracked VMs"""
        self.VM = None
        self.vm_list = Listbox(self.left_frame)
        self.vm_list.grid(row=1)
        for v in self.__vms:
            self.vm_list.insert(END, v.name)
        # TODO: Reintroduce this
        #self.graph_populate()
        self.poll_details()


    def update_details(self, selection):
        """Update bottom frame with vm details"""
        vm = self._vm_uuid[selection[0]]
        vm_ref = self._session.xenapi.VM.get_by_uuid(vm)
        # Attempt to clean up existing entries before we create the new ones
        try:
            self.details_label.destroy()
            self.name_label.destroy()
            self.vdi_label.destroy()
            self.date_label.destroy()
        except Exception as e:
            print(e)
            pass
        # Add row titles
        vm_string = "VM uuid: {}".format(vm)
        self.details_label = Label(self.bottom_frame, text=vm_string, anchor=W)
        self.details_label.grid(row=1, sticky='W')
        name = self.get_vm_name_label(vm)
        name_string = "Name label: {}".format(name)
        self.name_label = Label(self.bottom_frame, text=name_string, anchor=W)
        self.name_label.grid(row=2, sticky='W')
        # BackupConfig(session, back dir, use_tls)
        self.backup = BackUp.BackupConfig(self._session, "./", use_tls=False)
        # This call is now obsolete - should cache all the information about a VM
        """
        vdis = self.backup._get_vdis_of_vm(vm_ref)
        vdi_string = "VDIs: "
        for vdi in vdis:
            vdi_string += vdi + ";"
        self.vdi_label = Label(self.bottom_frame, text=vdi_string, anchor=W)
        self.vdi_label.grid(row=3, sticky='W')
        # Add info on last backup, total backups, etc
        self.c.execute("SELECT date FROM backups WHERE vm = (?) ORDER BY date DESC", (vm,))
        data = self.c.fetchall()
        print("DATA")
        if data:
          print(data[0][0])
          backup_date = "Last backup date: {}".format(data[0][0])
          self.date_label = Label(self.bottom_frame, text=backup_date, anchor=W)
          self.date_label.grid(row=4, sticky='W')
        """


    def poll_details(self):
        """Poll the vm list in the left frame to see when one is selected"""
        now = self.vm_list.curselection()
        print("selected1")
        print(now)
        if now != self.VM:
            print("now1")
            if now:
                print("test1")
                self.update_details(now)
                self.VM = now
        self.master.after(1000, self.poll_details)


    def populate_graph(self):
        """Populate graph in top frame"""
        pass


def main():
    try:
        session = XAPI.connect()
        root = Tk()
        root.geometry('{}x{}'.format(930, 500))
        app = App(root, session)
        root.mainloop()
    finally:
        root.destroy()
        session.xenapi.logout()

if __name__ == "__main__":
    main()