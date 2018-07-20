import sqlite3
import XenAPI

# Class to handle opening and closing database connections
class DbConnection(object):
    def __init__(self):
        self.__connect()
        self.create_table()

    def __connect(self):
        self.conn = sqlite3.connect("C:\\Users\Tom\Documents\pythonsqlite.db")
        print(sqlite3.version)
        self.c = self.conn.cursor()

    def create_table(self):
        # Try and create table
        try:
            self.c.execute('''CREATE TABLE hosts
                     (host_id integer primary key, host text, username text, password text)''')
            self.c.execute('''CREATE TABLE vms
                     (vm_id integer primary key, vm_uuid text, vm_name text, record text, tracked bool, host_id, 
                     FOREIGN KEY(host_id) REFERENCES hosts(host_id)''')
            self.c.execute('''CREATE TABLE backups
                     (date date, vm_id integer, FOREIGN KEY(vm_id) REFERENCES vms(vm_id))''')
            self.c.execute('''CREATE TABLE vdis
                                 (vdi_id integer primary key, vdi_uuid text, vdi_name text, record text, vm_id, 
                                 FOREIGN KEY(vm_id) REFERENCES vms(vm_id))''')
        except Exception as e:
            if "already exists" in str(e):
                pass
            else:
                raise e

    def query(self, query, params=None):
        try:
            self.c.execute(query, params)
            result = self.c.fetchall()
            return result
        except Exception as e:
            print(e)

    def insert(self, query, params):
        try:
            self.c.execute(query, params)
            self.conn.commit()
        except Exception as e:
            print(e)

    def __del__(self):
        self.conn.close()


class XAPI(object):
    _xapi_session = None

    @classmethod
    def connect(cls, disconnect_atexit=True):
        if cls._xapi_session is not None:
            return cls._xapi_session

        hostname = "lcy2-dt112.xenrt.citrite.net"
        username = "root"
        password = "xenroot"
        ignore_ssl = True

        if hostname == 'localhost':
            cls._xapi_session = XenAPI.xapi_local()
            username = ''
            password = ''
        else:
            cls._xapi_session = XenAPI.Session("http://%s/" % hostname, ignore_ssl=ignore_ssl)

            if not password:
                password = ''

        try:
            cls._xapi_session.login_with_password(username, password, '1.0', 'xenserver_guest.py')
        except XenAPI.Failure as f:
            module.fail_json(msg="Unable to log on to XenServer at %s as %s: %s" % (hostname, username, f.details))

        return cls._xapi_session