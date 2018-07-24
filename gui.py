from tkinter import *
from xs_objects import *
from connections import XAPI
import matplotlib
import numpy
import time
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
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
        # No need add VMs as we now track them all
        #filemenu.add_command(label="New VM", command=self.new_vm)
        # Move function to the VM class
        # filemenu.add_command(label="Backup", command=self.backup_vm)
        filemenu.add_command(label="Exit", command=quit)

        # If we have existing settings then gather them
        # TODO: If we have an error when connecting the first time we get stuck in loop till db is deleted
        # TODO: Create class to manage database connections

        # Just work with one host for now
        self.__local = Local()
        # Check if there are existing hosts in the database
        print("LOCAL %s %s" % (self.__local, self.__local.pre_existing))
        if self.__local.pre_existing:
            self.__host = self.__local.hosts[0]
            self.__vms = self.__host.vms
        # self._session = session
        self.populate_page()

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

    """
    def new_vm(self):
        v = new_vm_dialog(self.master, self._pool_master_address)
        vm_uuid = v.result
    """

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
        """Update bottom frame with vm/vdi details"""
        vm = self.__vms[selection[0]]
        #vm_ref = self._session.xenapi.VM.get_by_uuid(vm)
        # Attempt to clean up existing entries before we create the new ones
        try:
            self.details_label.destroy()
            self.name_label.destroy()
            #self.vdi_label.destroy()
            #self.date_label.destroy()
        except Exception as e:
            print(e)
            pass
        # Add row titles
        vm_string = "VM uuid: {}".format(vm.uuid)
        self.details_label = Label(self.bottom_frame, text=vm_string, anchor=W)
        self.details_label.grid(row=1, sticky='W')
        name = vm.name
        name_string = "Name label: {}".format(name)
        self.name_label = Label(self.bottom_frame, text=name_string, anchor=W)
        self.name_label.grid(row=2, sticky='W')
        # Get VDI information

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