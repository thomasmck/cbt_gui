import XenAPI
from connections import DbConnection

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
        self.save(self.__address, self.__username, self.__password)
        self.__session = None

    def __build_up(self, address, username, password):
        pass

    def save(self, address, username, password):
        self.c.execute("SELECT vm_uuid FROM vms")
        # TODO: Create class/function to handle db calls
        self.c.execute("SELECT host, username, password FROM hosts")
        host_details = self.c.fetchall()
        self._pool_master_address = host_details[0][0]
        self._username = host_details[0][1]
        self._password = host_details[0][2]

        DbConnection.insert("INSERT INTO hosts VALUES (?,?,?)", (self._pool_master_address, self._username, self._password,))

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

    def getMachine(self, uuid):
        pass

    def __buildVmList(self):
        pass


class VM(object):
    """
    Build and save VM objects
    """
    def __init__(self, uuid, host):
        self.__uuid = uuid
        self.build_up(uuid)
        self.__host = host

    def build_up(self, uuid):
        # See if VDI is cached
        try:
            pass
        # Otherwise find details from host
        except:
            pass

    @property
    def vdis(self):
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