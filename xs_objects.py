import XenAPI
from connections import DbConnection, XAPI
from xs_cbt_backup import backup as Backup

class Host(object):
    """
    Build and save Host objects
    """
    def __init__(self, name, username, password):
        """
        Constructor
        :param name: Name of a XS host
        :param username: Username of the host
        :param password: Password of the host
        """
        self.__vms = None
        self.__name = name
        self.__username = username
        self.__password = password
        self.__address = name + ".xenrt.citrite.net"
        self.__session = XAPI.connect()
        self.__db = DbConnection()
        self.save(self.__address, self.__username, self.__password)

    def __build_up(self, address, username, password):
        pass

    def save(self, address, username, password):
        # ToDo: Check there isn't an existing entry for this address
        """
        self.c.execute("SELECT host, username, password FROM hosts")
        host_details = self.c.fetchall()
        self._pool_master_address = host_details[0][0]
        self._username = host_details[0][1]
        self._password = host_details[0][2]
        """
        self.__db.insert("INSERT INTO hosts VALUES (?,?,?)", (address, username, password,))

    @property
    def name(self):
        return self.__name

    @property
    def address(self):
        return self.__address

    @property
    def vms(self):
        """
        User VMs on the host
        :return: Dict of vm instances
        """
        if not self.__vms:
            self.__buildVmList()
        return self.__vms

    def getVM(self, uuid):
        pass

    def __buildVmList(self):
        self.__vms = []
        vms_refs = [vm for vm in self._session.xenapi.VM.get_all() if not self._session.xenapi.VM.get_is_a_template(vm)]
        for vm_ref in vms_refs:
            vm_uuid = self.__session.xenapi.VM.get_uuid(vm_ref)
            self.__vms.append(VM(vm_uuid, self.__name, self.__session, self.__db))


class VM(object):
    """
    Build and save VM objects
    """
    def __init__(self, uuid, host, session, db):
        self.__uuid = uuid
        self.build_up(uuid)
        self.__host = host
        self.__session = session
        self.__vdis = None
        self.__db = db

    def build_up(self, uuid):
        # See if VDI is cached
        try:
            pass
        # Otherwise find details from host
        except:
            pass

    @property
    def vdis(self):
        if not self.__vdis:
            self.__buildVdiList()
        return self.__vdis

    @property
    def host(self):
        return self.__host

    @property
    def uuid(self):
        return self.__uuid

    def __buildVdiList(self):
        try:
            self.__fetchCachedVdis()
        except:
            self.__fetchUncachedVdis()

    def __fetchCachedVdis(self):
        self.__vdis = []
        # Add type (i.e. int) option to query
        vm_id = int(self.__db.query("SELECT vm_id FROM vms WHERE vm_uuid=(?)", (vm_uuid,))[0][0])
        vms = int(self.__db.query("SELECT vdi_uuid FROM vdis WHERE vm_id=(?)", (vm_id,))[0])
        for vm in vms:
            vdi_uuid = None
            self.__vdis.append(VDI(vdi_uuid))

    def __fetchUncachedVdis(self):
        self.__vdis = []
        vm_ref = self.__session.xenapi.VM.get_by_uuid(self.__uuid)
        vbd_refs = self._session.xenapi.VM.get_VBDs(vm_ref)
        print("VBD refs: %s" % vbd_refs)
        # (vdi_id integer primary key, vdi_uuid text, vdi_name text, record text, vm_id, FOREIGN KEY(vm_id) REFERENCES vms(vm_id))''')
        for vbd_ref in vbd_refs:
            vdi_ref = self._session.xenapi.VBD.get_VDI(vbd_ref)
            if vdi_ref == "OpaqueRef:NULL":
                continue
            vdi_uuid = self.__session.xenapi.VDI.get_uuid(vdi_ref)
            self.__vdis.append(VDI(vdi_uuid))
        #save()

    def save(self, uuid, name, record, vm_id):
        pass

    def __backup(self):
        # Backup a VM
        now = self.vm_list.curselection()
        vm = self._vm_uuid[now[0]]
        timestamp = self.__db.query("SELECT date('now')")[0][0]
        self.__db.insert("INSERT INTO backups VALUES (?,?)", (timestamp, vm))
        #def backup(master, vm, pwd, uname='root', tls=True):
        self.__backup = Backup.backup(self._pool_master_address, self.__uuid, self._password, tls=False)
        # Make a background task otherwise gui cannot be used
        location = self.__backup.backup()
        self.graph_populate()

    def __save_backup_details(self):
        pass

    def restore(self):
        pass


class VDI(object):
    """Object for a VDI"""
    def __init__(self, uuid):
        self.find_vdi(uuid)

    def find_vdi(self, uuid):
        # See if VDI is cached
        try:
            pass
        # Otherwise find details from host
        except:
            pass

    def save(self, uuid):
        vdi_ref = self._session.xenapi.VDI.get_by_uuid(uuid)
        if vdi_ref == "OpaqueRef:NULL":
            return
        vdi_name_label = self._session.xenapi.VDI.get_name_label(vdi_ref)
        print(vdi_name_label)
        vdi_uuid = self._session.xenapi.VDI.get_uuid(vdi_ref)
        print(vdi_uuid)
        vdi_record = str(self._session.xenapi.VDI.get_record(vdi_ref))
        print(vdi_record)
        # ToDo: Need mechanism to manage db connections
        self.c.execute("SELECT vm_id FROM vms WHERE vm_uuid=(?)", (vm_uuid,))
        vm_id = int(self.c.fetchall()[0][0])
        print("VM id: %s" % vm_id)
        self.c.execute("INSERT INTO vdis(vdi_uuid, vdi_name, record, vm_id) VALUES (?,?,?,?)",
                       (vdi_uuid, vdi_name_label, vdi_record, vm_id))
        self.conn.commit()