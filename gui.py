from tkinter import *
from tkinter import simpledialog as SimpleDialog
import backup as BackUp
import XenAPI
import matplotlib
import numpy
import time
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import sqlite3
from sqlite3 import Error

class App():

    def __init__(self, master):

        self.master = master
        self.setup()
        self._vdi = []
        self._vm_uuid = []
        self.prexisting = False

        # Create menu bar
        menu = Menu(self.master)
        self.master.config(menu=menu)
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=self.new_vdi)
        filemenu.add_command(label="Backup", command=self.backup_vm)
        filemenu.add_command(label="Exit", command=quit)

        self.connect_database()
        if not self.prexisting:
            self.new_host()
            self.new_vdi()
        else:
            self.get_existing_details()
        self._session = self.create_new_session()
        self.populate_page()

    def get_existing_details(self):
        self.c.execute("SELECT vm FROM tracked")
        vms = self.c.fetchall()
        for vm in vms:
            self._vm_uuid.append(vm[0])
        self.c.execute("SELECT host, username, password FROM host")
        host_details = self.c.fetchall()
        self._pool_master_address = host_details[0][0]
        self._username = host_details[0][1]
        self._password = host_details[0][2]

    def connect_database(self):
        """ create a database connection to a SQLite database """

        # TODO: Make this general or give dialog option
        self.conn = sqlite3.connect("C:\\Users\Tom\Documents\pythonsqlite.db")
        print(sqlite3.version)
        self.c = self.conn.cursor()

        # Create table
        try:
            self.c.execute('''CREATE TABLE backups
                     (date date, vm text)''')
            self.c.execute('''CREATE TABLE tracked
                     (vm text)''')
            self.c.execute('''CREATE TABLE host
                     (host text, username text, password text)''')
        except Exception as e:
            if "already exists" in str(e):
                print("Table already exists")
                self.prexisting = True
            else:
                raise e
        # conn.close()

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

    def get_details(self, object, type):
        """Function to get details i.e. name label for a given  object ref"""
        x = {"VDI": self._session.xenapi.VDI}
        print("get_details")
        details = {}
        print(details)


    def new_host(self):
        """Function to request details on host and create session with host"""
        d = new_host_dialog(self.master)
        self._pool_master_address, self._username, self._password = d.result
        self.c.execute("INSERT INTO host VALUES (?,?,?)", (self._pool_master_address, self._username, self._password))
        self.conn.commit()


    def new_vdi(self):
        """Launch dialog to get vm/vdi. Populate page with details"""
        v = new_vm_dialog(self.master)
        vm_uuid = v.result
        if vm_uuid not in self._vm_uuid:
            self._vm_uuid.append(vm_uuid)
            self.c.execute("INSERT INTO tracked VALUES (?)", (vm_uuid,))
            self.conn.commit()
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
        self.backup = BackUp.Backup(self._pool_master_address, self._username, self._password, vm)
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

        f = Figure(figsize=(5, 2), dpi=100)
        a = f.add_subplot(111)

        rects1 = a.bar(ind, y, width)
        #a.plot(x, y)

        self.canvas = FigureCanvasTkAgg(f, master=self.top_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().grid()
        #self.canvas.draw()
        print("HERE")

    def get_vm_name_label(self, uuid):
        ref = self._session.xenapi.VM.get_by_uuid(uuid)
        name = self._session.xenapi.VM.get_name_label(ref)
        return name


    def populate_page(self):
        """Function to populate left frame with tracked VMs"""
        self.VM = None
        self.vm_list = Listbox(self.left_frame)
        self.vm_list.grid(row=1)
        for v in self._vm_uuid:
            v_name = self.get_vm_name_label(v)
            self.vm_list.insert(END, v_name)
        self.graph_populate()
        self.poll_details()


    def update_details(self, selection):
        """Update bottom frame with vm details"""
        vm = self._vm_uuid[selection[0]]
        try:
            self.details_label.destroy()
            self.name_label.destroy()
        except:
            pass
        self.details_label = Label(self.bottom_frame, text=vm, anchor=W)
        self.details_label.grid(row=1, sticky='W')
        name = self.get_vm_name_label(vm)
        self.name_label = Label(self.bottom_frame, text=name, anchor=W)
        self.name_label.grid(row=2, sticky='W')
        self.backup = BackUp.Backup(self._pool_master_address, self._username, self._password, vm)
        vdis = self.backup._get_vdis_of_vm(vm)
        print(vdis)


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


class new_vm_dialog(SimpleDialog.Dialog):
    """Dialog for selecting new VM/VDI"""
    def create_new_session(self):
        session = XenAPI.Session("https://dt56.uk.xensource.com", ignore_ssl=True)
        session.login_with_password("root", "xenroot", "0.1", "CBT example")
        return session

    def body(self, master):
        self._session = self.create_new_session()
        Label(master, text="VM").grid(row=0)

        self.vm_listbox = Listbox(master)
        self.vm_listbox.grid(row=0, column=1)
        self.vm_listbox.insert(END, "Select a VM")

        VMs = self._session.xenapi.VM.get_all()
        self.VMs = []
        for VM in VMs:
            if not self._session.xenapi.VM.get_is_a_template(VM):
                self.VMs.append(VM)

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


def main():
    root = Tk()
    root.geometry('{}x{}'.format(930, 500))
    app = App(root)
    root.mainloop()
    root.destroy()

if __name__ == "__main__":
    main()


"""
    def setup2(self):
        # Create frame
        top_frame = Frame(self.master, bg='cyan', width=300, height=100, pady=3, padx=3)
        left_frame = Frame(self.master, bg='yellow', width=160, height=350, padx=3)
        btm_frame = Frame(self.master, bg='red', width=300, height=250, pady=3, padx=3)

        # layout all of the main containers
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

        top_frame.grid(row=0, column=1, sticky="nsew")
        left_frame.grid(rowspan=2, row=0, sticky="nsew")
        btm_frame.grid(row=1, column=1, sticky="nsew")

        # Create widgets
        name_label = Label(top_frame, text="Dummy text")
        vdi_label = Label(left_frame, text="VDIs")
        detail_label = Label(btm_frame, text="Details")

        # Layout the widgets
        name_label.grid()
        vdi_label.grid()
        detail_label.grid()

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
                self.results.append(key)"""