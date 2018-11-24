from xmlrpc.client import ServerProxy
import pprint

class attribute_builder:
    models = None
    common = None
    uid = None

    db = None
    password = None


    def __init__(self, hostname, database, username, password):
        # Checking the Odoo version is a good test to see if connection over XML-RPC works, so at least get that out of the
        # way before troubleshooting authentication problems next.
        self.common = ServerProxy('https://{}/xmlrpc/2/common'.format(hostname))
        # print("Version: {}".format(self.common.version()))

        self.db = database
        self.password = password

        # Login seems to do the same as authenticate (below).
        # uid = common.login(o_database, o_username, o_password)

        self.uid = self.common.authenticate(database, username, password, {})
        #print("authenticate: usermane={}, password={}, UID: {}".format(o_username, o_password, uid))
        if self.uid is False:
            print("Credentials Error, check username and password!")
            exit(1)

        self.models = ServerProxy('https://{}/xmlrpc/2/object'.format(hostname))

        print("Attribute Builder Ready!")

    def dump_attributes(self):
        output = self.models.execute_kw(self.db, self.uid, self.password,
                                        'product.attribute', 'search_read', [], {})
        # print("Output: {}".format(output))
        pprint.pprint(output)

    def attribute_exists(self, name):
        attributes = self.models.execute_kw(self.db, self.uid, self.password,
                                            'product.attribute', 'search_read', [], {'fields': ['id', 'name']})
        for attribute in attributes:
            if attribute["name"] == name:
                return True
        return False

    def create_attribute(self, name):
        attribute_id = self.models.execute_kw(self.db, self.uid, self.password,
                                        'product.attribute', 'create', [{'name': name}])
        # print("Output: {}".format(output))
        pprint.pprint(attribute_id)
        return attribute_id

    def get_attribute_id(self, name):
        attributes = self.models.execute_kw(self.db, self.uid, self.password,
                                            'product.attribute', 'search_read', [], {'fields': ['id', 'name']})
        for attribute in attributes:
            if attribute["name"] == name:
                return attribute["id"]
        return -1

    def dump_attribute_values(self):
        output = self.models.execute_kw(self.db, self.uid, self.password,
                                        'product.attribute.value', 'search_read', [], {})
        # print("Output: {}".format(output))
        pprint.pprint(output)

    def create_attribute_value(self, attribute_id, value):
        attribute = self.models.execute_kw(self.db, self.uid, self.password,
                                           'product.attribute', 'search_read', [[['id', '=', attribute_id]]],
                                           {'fields': ['id', 'name']})

        output = self.models.execute_kw(self.db, self.uid, self.password,
                                        'product.attribute.value', 'create',
                                        [{"attribute_id": attribute[0]["id"], "name": value}])
        # print("Output: {}".format(output))
        pprint.pprint(output)

    def get_attribute_value_id(self, attribute_id, name):
        attribute_values = self.models.execute_kw(self.db, self.uid, self.password,
                                                  'product.attribute.value', 'search_read',
                                                  [[['attribute_id', '=', attribute_id]]], {})
        pprint.pprint(attribute_values)
        for av in attribute_values:
            if av["name"] == name:
                return av["id"]
        return -1
