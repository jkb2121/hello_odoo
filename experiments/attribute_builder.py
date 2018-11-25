from xmlrpc.client import ServerProxy
import pprint
import json


class attribute_builder:
    models = None
    common = None
    uid = None

    db = None
    password = None

    def __init__(self, hostname, database, username, password):
        # Checking the Odoo version is a good test to see if connection over XML-RPC works, so at least get that out of
        # the way before troubleshooting authentication problems next.
        self.common = ServerProxy('https://{}/xmlrpc/2/common'.format(hostname))

        self.db = database
        self.password = password

        self.uid = self.common.authenticate(database, username, password, {})
        if self.uid is False:
            print("Credentials Error, check username and password!")
            exit(1)

        self.models = ServerProxy('https://{}/xmlrpc/2/object'.format(hostname))
        print("Attribute Builder Ready!")

    def dump_attributes(self):
        output = self.models.execute_kw(self.db, self.uid, self.password,
                                        'product.attribute', 'search_read', [], {})
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
        pprint.pprint(output)

    def create_attribute_value(self, attribute_id, value):
        attribute = self.models.execute_kw(self.db, self.uid, self.password,
                                           'product.attribute', 'search_read', [[['id', '=', attribute_id]]],
                                           {'fields': ['id', 'name']})

        output = self.models.execute_kw(self.db, self.uid, self.password,
                                        'product.attribute.value', 'create',
                                        [{"attribute_id": attribute[0]["id"], "name": value}])
        # pprint.pprint(output)
        # Maybe we need a return value indicating success or failure

    def get_attribute_value_id(self, attribute_id, name):
        attribute_values = self.models.execute_kw(self.db, self.uid, self.password,
                                                  'product.attribute.value', 'search_read',
                                                  [[['attribute_id', '=', attribute_id]]], {})
        for av in attribute_values:
            if av["name"] == name:
                return av["id"]
        return -1

    def import_attributes_from_csv(self, filename):
        try:
            with open(filename, 'r') as f:
                j = json.load(f)

                for attribute in j["attributes"]:
                    # print("Attribute: {}".format(attribute))
                    attribute_id = -1
                    attribute_id = self.get_attribute_id(attribute["name"])

                    # Create the attribute in Odoo if it doesn't exist.
                    if attribute_id == -1:
                        print("Attribute Not in Odoo yet: {}".format(attribute_id))
                        self.create_attribute(attribute["name"])
                        print("Attribute Created: {}".format(attribute_id))
                    else:
                        print("Attribute already in Odoo: {}, ID: {}".format(attribute["name"], attribute_id))
            return 1
        except:
            return -1

    def import_attribute_values_from_csv(self, filename):
        try:
            with open(filename, 'r') as f:
                j = json.load(f)

                for attribute in j["attributes"]:
                    print("Attribute: {}".format(attribute["name"]))
                    attribute_id = self.get_attribute_id(attribute["name"])

                    # Create the attribute in Odoo if it doesn't exist already.
                    if attribute_id == -1:
                        print("Attribute Not in Odoo yet: {}".format(attribute["name"]))
                        self.create_attribute(attribute["name"])
                        attribute_id = self.get_attribute_id(attribute["name"])
                        print("Attribute Created: {}".format(attribute_id))
                    else:
                        print("Attribute in Odoo: {}, ID: {}".format(attribute["name"], attribute_id))

                    if attribute_id == -1:
                        print("Failed to add attribute {} to Odoo!".format(attribute["name"]))
                        return -1

                    # Import the values next
                    for value in attribute["values"]:
                        print("Value: {}".format(value))

                        attribute_value_id = -1
                        attribute_value_id = self.get_attribute_value_id(attribute_id, value["name"])

                        if attribute_value_id == -1:
                            print("Attribute Value Not in Odoo yet: {}".format(value["name"]))
                            self.create_attribute_value(attribute_id, value["name"])
                            attribute_value_id = self.get_attribute_value_id(attribute_id, value["name"])
                            print("Attribute Value Created: {}".format(attribute_value_id))
                        else:
                            print("Attribute Value already in Odoo: {}, ID: {}".format(value["name"],
                                                                                       attribute_value_id))
            return 1
        except:
            return -1
