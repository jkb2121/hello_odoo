from xmlrpc.client import ServerProxy
import yaml
import sys
import pprint



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

# dump_item_data(o_database, uid, o_password, [[['id','=', '1104']]])
# dump_item_data(o_database, uid, o_password, [[['id','=', '1104']]], 'all')


#
# With the SKU ID (product variant ID, I suppose), I should be able to update any fields that I want on that object.
# Kind of clumsy because I don't think I have the syntax just right for the "code = sku" in the filter section.
#
def get_id_by_sku(o_db, o_uid, o_pw, sku):
    output = models.execute_kw(o_db, o_uid, o_pw,
                               'product.product', 'search_read',
                               [[['code', '=', sku]]],
                               {'fields': ['id', 'code']})
    pprint.pprint(output)
    for o in output:
        if o["code"] == sku:
            return o["id"]

    return -1

sku_id = get_id_by_sku(o_database, uid, o_password, 'F-MIRR-CARA')
print("SKU ID: {}".format(sku_id))

# This is the example JSON I want to build:
pj = {
    'product': {
        'id': 12345,
        'type': 'product',
        'name': 'Nagoya Nightstand',
        'attribute_ids': [1],               # Finish
        'attribute_value_ids': [1, 2],      # Caramelized, Sable
        'variants': [
            {
                'code': 'F-NS-CARA',
                'type': 'product',
                'attribute_ids': [1],
                'attribute_value_ids': [1]
            },
            {
                'code': 'F-NS-SABL',
                'type': 'product',
                'attribute_ids': [1],
                'attribute_value_ids': [2]
            }
        ]
    }
}


print("Product: {}".format(pj['product']['id']))
print("SKU 1: {}".format(pj['product']['variants'][0]['code']))
print("SKU 2: {}".format(pj['product']['variants'][1]['code']))






