from connections import DbConnection, XAPI
from xs_cbt_backup import backup as Backup
import ast
from datetime import *

class Local(object):
    """
    Find information about existing local backup instances
    """
    def __init__(self):
        self.__hosts = None
        self.__db = DbConnection()
        self.__db.create_table()
        pass

    @property
    def pre_existing(self):
        if self.hosts:
            return True
        return False

    @property
    def hosts(self):
        if not self.__hosts:
            self.__buildHostList()
        return self.__hosts

    @property
    def db(self):
        return self.__db

    def __buildHostList(self):
        self.__hosts = []
        # Fetch host details from the database
        host_details = self.__db.query("SELECT host, username, password FROM hosts")
        if host_details:
            for hosts in host_details:
                name = hosts[0]
                username = hosts[1]
                password = hosts[2]
                self.__hosts.append(Host(name, username, password, self.__db))


class Host(object):
    """
    Build and save Host objects
    """
    def __init__(self, name, username, password, db):
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
        #self.__address = name + ".xenrt.citrite.net"
        # TEMP
        self.__address = name
        self.__session = XAPI.connect()
        self.__db = db
        # TODO: Only save if not pre-existing
        self.__save()
        self.__buildUp()

    def __buildUp(self):
        """
        Build up additional details on the host from the host record
        :return:
        """
        pass

    def __save(self):
        # ToDo: Check there isn't an existing entry for this address
        try:
            existing = int(self.__db.query("SELECT host_id FROM hosts WHERE host=(?)",  (self.__address,))[0][0])
            print("Not saving")
        except:
            print("Saving")
            self.__db.insert("INSERT INTO hosts(host, username, password) VALUES (?,?,?)", (self.__address,
                             self.__username, self.__password,))

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
        try:
            self.__fetchCachedVms()
        except:
            self.__fetchUncachedVms()

    def __fetchCachedVms(self):
        self.__vms = []
        # Add type (i.e. int) option to query
        host_id = int(self.__db.query("SELECT host_id FROM vms WHERE host=(?)", (self.__address,))[0][0])
        # Need to verify this correctly handles return format
        vms = int(self.__db.query("SELECT vm_uuid FROM vms WHERE host_id=(?)", (host_id,))[0])
        for vm in vms:
            vdi_uuid = None
            self.__vms.append(VM(vm, self, self.__session, self.__db))

    def __fetchUncachedVms(self):
        self.__vms = []
        vms_refs = [vm for vm in self.__session.xenapi.VM.get_all() if not self.__session.xenapi.VM.get_is_a_template(vm)]
        for vm_ref in vms_refs:
            vm_uuid = self.__session.xenapi.VM.get_uuid(vm_ref)
            self.__vms.append(VM(vm_uuid, self, self.__session, self.__db))


class VM(object):
    """
    Build and save VM objects
    """
    def __init__(self, uuid, host, session, db):
        self.__uuid = uuid
        self.__host = host
        self.__session = session
        self.__vdis = None
        self.__db = db
        self.__buildUp(uuid)
        self.__save()

    def __buildUp(self, uuid):
        """
        Build up additional VM details
        :param uuid:
        :return:
        """
        self.__ref = self.__session.xenapi.VM.get_by_uuid(uuid)
        self.__name = self.__session.xenapi.VM.get_name_label(self.__ref)
        pass

    @property
    def vdis(self):
        if not self.__vdis:
            self.__buildVdiList()
        return self.__vdis

    @property
    def name(self):
        return self.__name

    @property
    def host(self):
        return self.__host

    @property
    def uuid(self):
        return self.__uuid

    def __buildVdiList(self):
        # Try grabbing cached results if the exist
        try:
            self.__fetchCachedVdis()
            print("CACHED")
        except:
            self.__fetchUncachedVdis()
            print("UNCACHED")

    def __fetchCachedVdis(self):
        #self.__vdis = {self.__name: []}
        self.__vdis = []
        # Add type (i.e. int) option to query
        print("a")
        vm_id = int(self.__db.query("SELECT vm_id FROM vms WHERE vm_uuid=(?)", (self.__uuid,))[0][0])
        print(vm_id)
        vdis = self.__db.query("SELECT vdi_uuid FROM vdis WHERE vm_id=(?)", (vm_id,))[0]
        print(vdis)
        for vdi in vdis:
            vdi_uuid = None
            #self.__vdis[self.__name].append(VDI(vdi_uuid, self.__uuid, self.__db, self.__session))
            self.__vdis.append(VDI(vdi, self, self.__db, self.__session))

    # THIS FUNCTION IS BEING CALLED EVEN WHEN VDIS ARE CACHED
    def __fetchUncachedVdis(self):
        self.__vdis = []
        vm_ref = self.__session.xenapi.VM.get_by_uuid(self.__uuid)
        vbd_refs = self.__session.xenapi.VM.get_VBDs(vm_ref)
        print("VBD refs: %s" % vbd_refs)
        # (vdi_id integer primary key, vdi_uuid text, vdi_name text, record text, vm_id, FOREIGN KEY(vm_id) REFERENCES vms(vm_id))''')
        for vbd_ref in vbd_refs:
            vdi_ref = self.__session.xenapi.VBD.get_VDI(vbd_ref)
            if vdi_ref == "OpaqueRef:NULL":
                continue
            vdi_uuid = self.__session.xenapi.VDI.get_uuid(vdi_ref)
            self.__vdis.append(VDI(vdi_uuid, self, self.__db, self.__session))

    def __save(self):
        try:
            existing = int(self.__db.query("SELECT vm_id FROM vms WHERE vm_uuid=(?)",  (self.__uuid,))[0][0])
            print("Not saving")
        except:
            print("Saving")
            record_string = str(self.__session.xenapi.VM.get_record(self.__ref))
            # (vm_id integer primary key, vm_uuid text, vm_name text, record text, tracked bool)
            self.__db.insert("INSERT INTO vms(vm_uuid, vm_name, record, tracked) VALUES (?,?,?,?)",
                            (self.__uuid, self.__name, record_string, "True"))

    def backup(self):
        # Backup a VM
        # Record backup in table
        #timestamp = self.__db.query("SELECT date('now')")[0][0]

        # Initiate backup
        # TODO: handle this in a thread
        # def __init__(self, session, backup_dir, use_tls):
        self.__backup = Backup.BackupConfig(self.__session, "C:\\Users\Tom\Documents\.backup", False)
        #def backup(self, vm_uuid):
        timestamp = self.__backup.backup(self.__uuid)
        self.__db.insert("INSERT INTO backups VALUES (?,?)", (timestamp, self.__uuid))
        #location = self.__backup.backup()

        # Update backup graph
        self.graph_populate()

    def __save_backup_details(self):
        """
        Save record with details of the backup
        :return:
        """
        pass

    def restore(self):
        """
        Restore the VM
        :return:
        """
        pass


class VDI(object):
    """Object for a VDI"""
    def __init__(self, uuid, vm, db, session):
        self.__uuid = uuid
        self.__vm = vm
        self.__db = db
        self.__session = session
        self.__save()
        self.__buildUp()

    @property
    def name(self):
        return self.__name

    @property
    def uuid(self):
        return self.__uuid

    @property
    def virtual_size(self):
        return self.__virtual_size

    @property
    def record(self):
        return self.__record

    def get_record(self, name):
        if name in self.__record.keys():
            return self.__record[name]
        return

    def __buildUp(self):
        """
        Build up additional VDI details
        :return: None
        """
        self.__ref = self.__session.xenapi.VDI.get_by_uuid(self.__uuid)
        (self.__id, uuid, self.__name, record, vm_id) = self.__db.query("SELECT * FROM vdis WHERE vdi_uuid=(?)", (self.__uuid,))[0]

        # Return to dict format
        self.__record = ast.literal_eval(record)
        # TODO: consider other entries we may want to make properties
        self.__virtual_size = self.__record['virtual_size']

    def __save(self):
        # Maybe should move this logic to the cached/uncached VDI stuff in the VM class?
        try:
            existing = int(self.__db.query("SELECT vdi_id FROM vdis WHERE vdi_uuid=(?)",  (self.__uuid,))[0][0])
            print("Not saving")
        except:
            vdi_ref = self.__session.xenapi.VDI.get_by_uuid(self.__uuid)
            self.__name = self.__session.xenapi.VDI.get_name_label(vdi_ref)
            vdi_record = self.__session.xenapi.VDI.get_record(vdi_ref)
            # Remove this record as it causes issues when being evaluated later
            # TODO: consider converting to json instead so we don't need to use eval to read
            vdi_record['snapshot_time'] = "NULL"
            vm_id = int(self.__db.query("SELECT vm_id FROM vms WHERE vm_uuid=(?)", (self.__vm.uuid,))[0][0])
            self.__db.insert("INSERT INTO vdis(vdi_uuid, vdi_name, record, vm_id) VALUES (?,?,?,?)",
                             (self.__uuid, self.__name, str(vdi_record), vm_id))
