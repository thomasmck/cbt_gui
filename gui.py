from tkinter import *
from xs_objects import *
from connections import XAPI
import matplotlib
import numpy
import time
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from gui_dialog import new_host_dialog


class App():

    def __init__(self, master, session):

        self.__vdis = []
        self.__vms = []
        self.master = master
        self.setup_frame()
        self.setup_menu()
        self.gather_existing_data()
        self.populate_page()
        self.__backup_threads = {}
        self.progress_labels = []

    def setup_menu(self):
        # Create menu bar
        # Does this need to be self?
        menu = Menu(self.master)
        self.master.config(menu=menu)

        # File dropdown menu
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New host", command=self.new_host)
        filemenu.add_command(label="Exit", command=quit)

        # VM drop down menu
        vmmenu = Menu(menu)
        menu.add_cascade(label="VM", menu=vmmenu)
        vmmenu.add_command(label="Backup", command=self.backup_vm)

    def gather_existing_data(self):
        # Just work with one host for now
        self.__local = Local()
        # Check if there are existing hosts in the database
        print("LOCAL %s %s" % (self.__local, self.__local.pre_existing))
        if self.__local.pre_existing:
            self.__host = self.__local.hosts[0]
            self.__vms = self.__host.vms
            self.__vdis = {}
            for vm in self.__vms:
                self.__vdis[vm.name] = vm.vdis

    def setup_frame(self):
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

        # Height options have no impact :(
        self.progess_frame = Frame(self.master, bg='blue', height=50)
        self.m2.add(self.progess_frame, height=50)
        self.m2.paneconfigure(self.progess_frame, height=2)

        Label(self.left_frame, text="VMs", width=30).grid(row=0, sticky='W')
        Label(self.top_frame, text="Graphs", width=100).grid(row=0, sticky='W')
        Label(self.bottom_frame, text="Details", width=100).grid(row=0, sticky='W')

    def new_host(self):
        """Function to request details on host and create session with host"""
        d = new_host_dialog(self.master)
        address, username, password = d.result
        self.__host = Host(address, username, password, self.__local.db)
        self.__vms = self.__host.vms
        self.__vdis = {}
        for vm in self.__vms:
            self.__vdis[vm.name] = vm.vdis
        print("VMS: %s" % self.__vms)
        self.populate_page()

    def backup_vm(self):
        vm = self.__vms[self.VM[0]]
        backup_thread = vm.backup()
        self.__backup_threads[backup_thread.name] = backup_thread
        # Start process to track thread status
        self.__track_thread_status()

    def __track_thread_status(self):
        # This probably needs to be a thread as well
        # To find progress we need to compare the size of the current file we are writing vs. the virtual size
        for thread in self.__backup_threads:
            if thread.is_alive():
                self.__update_progress(thread)
            else:
                # Once a thread is complete update the graph then remove it from the list
                self.graph_populate()
                self.__backup_threads.remove(thread)
        # Poll every 5 seconds
        self.master.after(5000, self.__track_thread_status())

    def __update_progress(self, thread):
        def create_label(self, text, row):
            label = Label(self.progess_frame, text=text, anchor=W)
            label.grid(row=row, sticky='W')
            return label

        """Update progress frame with vm backup progress"""

        # Attempt to clean up existing entries before we create the new ones
        try:
            for label in self.progress_labels:
                label.destroy()
        except Exception as e:
            print(e)

        # Calculate percent_comlete by comparing the file size to the VDI virtual/physical size.
        # For incremental backup would need to add function to xs_cbt_backup code to track progress of iteration
        # through bitmap
        percent_completion = None
        progess = "%s: %s \%" %(thread.name, percent_completion)
        # Need to adjust row
        self.progress_labels.append(create_label(self, progess, 1))

    def graph_populate(self):
        """Generate graph of how many backups have been done each day"""
        # Clear any existing widgets
        try:
            self.canvas.get_tk_widget().destroy()
        except Exception as e:
            print(e)
            pass

        # Add 0 entries for empty days
        self.__db.query("SELECT date, count(date) FROM backups WHERE date BETWEEN datetime('now', '-6 days') AND datetime('now', 'localtime') GROUP BY date ORDER BY date ASC")
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

        def create_label(self, text, row):
            label = Label(self.bottom_frame, text=text, anchor=W)
            label.grid(row=row, sticky='W')
            return label

        """Update bottom frame with vm/vdi details"""

        # Find currently selected vm
        vm = self.__vms[selection[0]]

        # Attempt to clean up existing entries before we create the new ones
        try:
            self.vm_uuid_label.destroy()
            self.name_label.destroy()
            for label in self.vdi_labels:
                label.destroy()
        except Exception as e:
            print(e)

        # Add vm uuid row
        vm_uuid = "VM uuid: {}".format(vm.uuid)
        self.vm_uuid_label = create_label(self, vm_uuid, 1)

        # Add vm name label row
        vm_name = "Name label: {}".format(vm.name)
        self.name_label = create_label(self, vm_name, 2)

        # Add VDI details row
        vdis = self.__vdis[vm.name]
        self.vdi_labels = []
        print("VDIS: %s" %vdis)

        vdi_name = "----VDIs-----"
        vdi_section_label = create_label(self, vdi_name, 3)
        self.vdi_labels.append(vdi_section_label)

        gap = "-------------------"
        row = 4
        for vdi in vdis:
            # Vdi name label
            vdi_name = "Name label: {}".format(vdi.name)
            vdi_name_label = create_label(self, vdi_name, row)
            self.vdi_labels.append(vdi_name_label)

            # Vdi uuid label
            vdi_uuid = "Name label: {}".format(vdi.uuid)
            vdi_uuid_label = create_label(self, vdi_uuid, row+1)
            self.vdi_labels.append(vdi_uuid_label)
            row = row + 2

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
