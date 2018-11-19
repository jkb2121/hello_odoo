from xmlrpc.client import ServerProxy
import yaml
import sys

import experiments

o_hostname = ''
o_username = ''
o_password = ''
o_database = ''

# ----------------------------------------------------------------------------------------------------------------------
if len(sys.argv) != 2:
    print("Usage:  hello_odoo.py <config>.yaml")
    exit(1)
else:
    try:
        print("Using Configuration File: " + sys.argv[1])
        with open(sys.argv[1], 'r') as f:
            yml = yaml.load(f)
            o_hostname = yml['odoo_settings']['hostname']
            o_username = yml['odoo_settings']['username']
            o_password = yml['odoo_settings']['password']
            o_database = yml['odoo_settings']['database']

    except IOError:
        print("Error Opening Config File: " + sys.argv[1])
        exit(1)

# Checking the Odoo version is a good test to see if connection over XML-RPC works, so at least get that out of the
# way before troubleshooting authentication problems next.
common = ServerProxy('https://{}/xmlrpc/2/common'.format(o_hostname))
print("Version: {}".format(common.version()))

# Login seems to do the same as authenticate (below).
# uid = common.login(o_database, o_username, o_password)

uid = common.authenticate(o_database, o_username, o_password, {})
print("authenticate: usermane={}, password={}, UID: {}".format(o_username, o_password, uid))
if uid is False:
    print("Credentials Error, check username and password!")
    exit(1)

models = ServerProxy('https://{}/xmlrpc/2/object'.format(o_hostname))


# Created this dump_item_data function so I can print out different things about Odoo Products.
def dump_item_data(o_db, o_uid, o_pw, filters=[], fields=''):
    if fields == '':
        fields = {'fields': ['id', 'name', 'code', 'product_variant_ids', 'product_variant_id', 'product_tmpl_id',
                             'display_name', 'attribute_line_ids', 'attribute_value_ids']}
    if fields == 'all':
        fields = ''

    print("---------------------------------------------------")
    print("All Item Data:")
    output = models.execute_kw(o_db, o_uid, o_pw,
                               'product.product', 'search_read',
                               filters,
                               fields)
    print("Output: {}".format(output))
    print("---------------------------------------------------")
    return output

dump_item_data(o_database, uid, o_password, [[['id','=', '1104']]])
dump_item_data(o_database, uid, o_password, [[['id','=', '1104']]], 'all')


