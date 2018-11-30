from xmlrpc.client import ServerProxy
import yaml
import sys
import pprint

import ssl
#print(ssl.get_default_verify_paths())

from experiments.attribute_builder import attribute_builder

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
common = ServerProxy('https://{}/xmlrpc/2/common'.format(o_hostname), verbose=False, use_datetime=True,
                     context=ssl._create_unverified_context())
# print("Version: {}".format(common.version()))

# Login seems to do the same as authenticate (below).
# uid = common.login(o_database, o_username, o_password)

uid = common.authenticate(o_database, o_username, o_password, {})
# print("authenticate: usermane={}, password={}, UID: {}".format(o_username, o_password, uid))
if uid is False:
    print("Credentials Error, check username and password!")
    exit(1)

models = ServerProxy('https://{}/xmlrpc/2/object'.format(o_hostname), verbose=False, use_datetime=True,
                     context=ssl._create_unverified_context())


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

# Set the Inventory Quantity and Standard Cost
def set_inventory_qty(o_db, o_uid, o_pw, variant_id, qty_on_hand, std_cost=0.01):

    print("Setting Variant ID {} to {} On Hand at {} Unit Cost".format(variant_id, qty_on_hand, std_cost))
    output = models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'write', [[variant_id], {
        'standard_price': std_cost,
        'qty_available': qty_on_hand,
        'qty_at_date': qty_on_hand,
        'virtual_available': qty_on_hand,
        'product_qty': qty_on_hand,
    }])
    print("Resulting in....")
    pprint.pprint(output)

    return output

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

# sku_id = get_id_by_sku(o_database, uid, o_password, 'F-MIRR-CARA')
# print("SKU ID: {}".format(sku_id))

# This is the example JSON I want to build:
# pj = {
#     'product': {
#         'id': 12345,
#         'type': 'product',
#         'name': 'Nagoya Nightstand',
#         'attribute_ids': [1],               # Finish
#         'attribute_value_ids': [1, 2, 4],      # Caramelized, Sable, Dark Walnut
#         'variants': [
#             {
#                 'code': 'F-NS-CARA',
#                 'type': 'product',
#                 'attribute_ids': [1],
#                 'attribute_value_ids': [1]
#             },
#             {
#                 'code': 'F-NS-SABL',
#                 'type': 'product',
#                 'attribute_ids': [1],
#                 'attribute_value_ids': [2]
#             },
#             {
#                 'code': 'F-NS-DWAL',
#                 'type': 'product',
#                 'attribute_ids': [1],
#                 'attribute_value_ids': [4]
#             }
#
#         ]
#     }
# }

# print("Product: {}".format(pj['product']['id']))
# print("SKU 1: {}".format(pj['product']['variants'][0]['code']))
# print("SKU 2: {}".format(pj['product']['variants'][1]['code']))
# print("SKU 2: {}".format(pj['product']['variants'][2]['code']))


# def build_odoo_product_from_json(o_db, o_uid, o_pw, j):
#     print("Building Odoo Product from JSON")
#
#     # Create the "Product" via the Product.Template
#     prod_tmpl_id = models.execute_kw(o_db, o_uid, o_pw, 'product.template', 'create', [{
#         'name': j['product']['name'],
#         'type': j['product']['type'],
#         'attribute_line_id': j['product']['attribute_ids'][0],
#         'attribute_value_ids': [(6, 0, j['product']['variants'][0]['attribute_value_ids'][0])]
#     }])
#     print("Product Template ID: {}".format(prod_tmpl_id))
#
#     # Create Product Attributes
#     attribute_line = models.execute_kw(o_db, o_uid, o_pw, 'product.attribute.line', 'create', [{
#         'product_tmpl_id': int(prod_tmpl_id),
#         'attribute_id': j['product']['attribute_ids'][0],
#         'value_ids': [(6, 0, j['product']['attribute_value_ids'])]
#     }])
#     print("Attribute_Line: {}".format(attribute_line))
#
#     # Get the Product ID Created by the Template
#     sku_output = models.execute_kw(o_db, o_uid, o_pw, 'product.template', 'search_read',
#                                    [[['id', '=', prod_tmpl_id]]],
#                                    {'fields': ['product_variant_ids']}
#                                    )
#     sku1 = sku_output[0]['product_variant_ids'][0]
#
#     i = 0
#     for variant in j['product']['variants']:
#
#         if i == 0:
#             # Write the First Variant (created by default)
#             models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'write', [[sku1], {
#                 'default_code': variant['code'],
#                 'code': variant['code'],
#                 'attribute_value_ids': [(6, 0, variant['attribute_value_ids'])]
#             }])
#         else:
#             models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'create', [{
#                 'default_code': variant['code'],
#                 'code': variant['code'],
#                 'product_tmpl_id': prod_tmpl_id,
#                 'type': 'product',
#                 'attribute_line_id': j['product']['attribute_ids'][0],
#                 'attribute_value_ids': [(6, 0, variant['attribute_value_ids'])]
#             }])
#
#         i += 1

# build_odoo_product_from_json(o_database, uid, o_password, pj)

# Instantiate the Attribute Builder
ab = attribute_builder(o_hostname, o_database, o_username, o_password)

# Dump the Attributes already in Odoo
# ab.dump_attributes()

# Print whether these attributes exist (should initially be "no")  Then create the attributes and try again...
# if ab.attribute_exists("Size"):
#     print("Size Exists")
# else:
#     print("Size does not Exist")
# ab.create_attribute("Size")

# Get at the Attribute ID from the Attribute Name
# print("Attribute ID for Finish: {}".format(ab.get_attribute_id("Finish")))
# print("Attribute ID for Size: {}".format(ab.get_attribute_id("Size")))

# Dump all of the Attribute Values
# ab.dump_attribute_values()

# Create an Attribute Value for an existing Attribute
# ab.create_attribute_value(1, "Hemlock")
# ab.dump_attribute_values()

# Print Attribute Value Information
# print("Attribute Value ID for Finish:Hemlock: {}".format(ab.get_attribute_value_id(1, "Hemlock")))
# print("Attribute Value ID for Size:XL: {}".format(ab.get_attribute_value_id(2, "XL")))

# Import all of the Attributes and Attribute Values from my JSON build files.
# ab.import_attributes_from_csv("work/attributes.json")
# ab.import_attribute_values_from_csv("work/attribute_values.json")

# Route ID's:  5 = Buy, 6 = Drop Ship

mjps = {
    "products": [
        {
            "id": "7777",
            "name": "Raku High Rise Bed",
            "prod_id": "1439",
            "type": "product",
            "route_ids": [6],
            "variants": [
                {
                    "sku": "F-RAKU-HI-F-D.WAL",
                    "price": 649,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Full"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Full / Dark Walnut",
                            "supplier_code": "10001",
                            "supplier_cost": 298
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-F-H.OAK",
                    "price": 649,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Full"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Full / Honey Oak",
                            "supplier_code": "10002",
                            "supplier_cost": 298
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-F-NAT",
                    "price": 649,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Full"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Full / Natural",
                            "supplier_code": "10003",
                            "supplier_cost": 298
                        }
                    ]
                },

                {
                    "sku": "F-RAKU-HI-K-D.WAL",
                    "price": 849,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "King"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku King / Dark Walnut",
                            "supplier_code": "10004",
                            "supplier_cost": 345
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-K-H.OAK",
                    "price": 849,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "King"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku King / Honey Oak",
                            "supplier_code": "10005",
                            "supplier_cost": 345
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-K-NAT",
                    "price": 849,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "King"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku King / Natural",
                            "supplier_code": "10006",
                            "supplier_cost": 345
                        }
                    ]
                },

                {
                    "sku": "F-RAKU-HI-Q-D.WAL",
                    "price": 749,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Queen"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Queen / Dark Walnut",
                            "supplier_code": "10007",
                            "supplier_cost": 308
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-Q-H.OAK",
                    "price": 749,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Queen"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Queen / Honey Oak",
                            "supplier_code": "10008",
                            "supplier_cost": 308
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-Q-NAT",
                    "price": 749,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Queen"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Queen / Natural",
                            "supplier_code": "10009",
                            "supplier_cost": 308
                        }
                    ]
                },

                {
                    "sku": "F-RAKU-HI-TXL-D.WAL",
                    "price": 599,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin XL"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Twin XL / Dark Walnut",
                            "supplier_code": "10010",
                            "supplier_cost": 255
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-TXL-H.OAK",
                    "price": 599,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin XL"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Twin XL / Honey Oak",
                            "supplier_code": "10011",
                            "supplier_cost": 255
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-TXL-NAT",
                    "price": 599,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin XL"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Twin XL / Natural",
                            "supplier_code": "10012",
                            "supplier_cost": 255
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-T-D.WAL",
                    "price": 599,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Twin / Dark Walnut",
                            "supplier_code": "10013",
                            "supplier_cost": 245
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-T-H.OAK",
                    "price": 599,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Twin / Honey Oak",
                            "supplier_code": "10014",
                            "supplier_cost": 245
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HI-T-NAT",
                    "price": 599,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Twin / Natural",
                            "supplier_code": "10015",
                            "supplier_cost": 245
                        }
                    ]
                }

            ]
        },
        {
            "id": "7778",
            "name": "Raku Headboard",
            "prod_id": "1440",
            "type": "product",
            "route_ids": [6],
            "variants": [
                {
                    "sku": "F-RAKU-HB-F-DW",
                    "price": 199,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Full"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Full / Dark Walnut",
                            "supplier_code": "10016",
                            "supplier_cost": 103
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-F-HO",
                    "price": 199,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Full"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Full / Honey Oak",
                            "supplier_code": "10017",
                            "supplier_cost": 103
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-F-NAT",
                    "price": 199,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Full"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Full / Natural",
                            "supplier_code": "10018",
                            "supplier_cost": 103
                        }
                    ]
                },

                {
                    "sku": "F-RAKU-HB-K-DW",
                    "price": 249,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "King"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard King / Dark Walnut",
                            "supplier_code": "10019",
                            "supplier_cost": 115
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-K-HO",
                    "price": 249,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "King"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard King / Honey Oak",
                            "supplier_code": "10020",
                            "supplier_cost": 115
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-K-NAT",
                    "price": 249,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "King"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard King / Natural",
                            "supplier_code": "10021",
                            "supplier_cost": 115
                        }
                    ]
                },

                {
                    "sku": "F-RAKU-HB-Q-DW",
                    "price": 229,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Queen"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Queen / Dark Walnut",
                            "supplier_code": "10022",
                            "supplier_cost": 105
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-Q-HO",
                    "price": 229,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Queen"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Queen / Honey Oak",
                            "supplier_code": "10023",
                            "supplier_cost": 105
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-Q-NAT",
                    "price": 229,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Queen"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Queen / Natural",
                            "supplier_code": "10024",
                            "supplier_cost": 105
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-T-DW",
                    "price": 199,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin/Twin XL"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Dark Walnut"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Twin/Twin XL / Dark Walnut",
                            "supplier_code": "10025",
                            "supplier_cost": 73
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-T-HO",
                    "price": 199,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin/Twin XL"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Honey Oak"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Twin/Twin XL / Honey Oak",
                            "supplier_code": "10026",
                            "supplier_cost": 73
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-HB-T-NAT",
                    "price": 199,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin/Twin XL"
                        },
                        {
                            "name": "Wood Finish",
                            "value": "Natural"
                        }

                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Headboard Twin/Twin XL / Natural",
                            "supplier_code": "10027",
                            "supplier_cost": 73
                        }
                    ]
                }

            ]
        },
        {
            "id": "7779",
            "name": "Raku Tatami Mat",
            "prod_id": "1441",
            "type": "product",
            "route_ids": [6],
            "variants": [
                {
                    "sku": "F-RAKU-TATAMI-F",
                    "price": 199.50,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Full"
                        }
                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Tatami Mat Full",
                            "supplier_code": "10028",
                            "supplier_cost": 85
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-TATAMI-Q",
                    "price": 199.50,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Queen"
                        }
                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Tatami Mat Queen",
                            "supplier_code": "10029",
                            "supplier_cost": 85
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-TATAMI-T",
                    "price": 229,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "Twin"
                        }
                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Tatami Mat Twin",
                            "supplier_code": "10030",
                            "supplier_cost": 102
                        }
                    ]
                },
                {
                    "sku": "F-RAKU-TATAMI-TXL/K",
                    "price": 249,
                    "attributes": [
                        {
                            "name": "Mattress Size",
                            "value": "King"
                        }
                    ],
                    "suppliers": [
                        {
                            "supplier_odoo_id": 16,
                            "supplier_name": "Lin's Oriental",
                            "supplier_product_name": "Lin's Raku Tatami Mat TwinXL/King",
                            "supplier_code": "10031",
                            "supplier_cost": 102
                        }
                    ]
                }

            ]
        }
    ]
}

# Twin/Twin XL


def build_odoo_product_from_json_multi(o_db, o_uid, o_pw, j):
    print("Building Odoo Product from JSON (multi)")

    #pprint.pprint(j)
    print("Product ID/Name/Type: {} / {}  {}".format(j["prod_id"], j["name"], j["type"]))

    # Create Array of Attributes/Values Dictionaries so that we can build the necessary Attribute/Values
    # relationships on the Product Template, Product Variants and Attribute Lines
    attribute_line_ids = []
    attribute_value_ids = []
    attr = []
    for pav in j['variants']:
        for a in pav["attributes"]:
            print("-SKU: {}: Attribute: {}: Value: {}".format(pav["sku"], a["name"], a["value"]))
            attr_id = ab.get_attribute_id(a["name"])
            av_id = ab.get_attribute_value_id(attr_id, a["value"])

            xfound = False
            for x in attr:
                if x["id"] == attr_id:
                    yfound = False
                    for y in x["values"]:
                        if y["id"] == av_id:
                            yfound = True
                            break
                    if yfound == False:
                        x["values"].append({"id": av_id, "name": a["value"]})
                        attribute_value_ids.append(av_id)
                    xfound = True
            if xfound is False:
                attr.append({"name": a["name"], "id": attr_id, "values": [{"id": av_id, "name": a["value"]}]})
                attribute_line_ids.append(attr_id)
    # pprint.pprint(attr)

    print("Attribute_Values Array: {}".format(attribute_value_ids))

    # Create the "Product" via the Product.Template
    prod_tmpl_id = models.execute_kw(o_db, o_uid, o_pw, 'product.template', 'create', [{
        'name': j['name'],
        'type': j['type'],
        'route_ids': [(6, 0, j['route_ids'])],
        'attribute_line_id': [(6, 0, attribute_line_ids)],
        'attribute_value_ids': [(6, 0, attribute_value_ids)]
    }])
    print("Product Template ID: {}".format(prod_tmpl_id))


    # # Get the Product ID Created by the Template
    sku_output = models.execute_kw(o_db, o_uid, o_pw, 'product.template', 'search_read',
                                   [[['id', '=', prod_tmpl_id]]],
                                   {'fields': ['product_variant_ids']}
                                   )
    sku1 = sku_output[0]['product_variant_ids'][0]

    # Create Product Attributes Association
    # For each Attribute, associate it with the Product Template by providing the Attribute ID and All Values
    for a in attr:
        av = []
        for aa in a["values"]:
            av.append(aa["id"])
        attribute_line = models.execute_kw(o_db, o_uid, o_pw, 'product.attribute.line', 'create', [{
            'product_tmpl_id': int(prod_tmpl_id),
            'attribute_id': a["id"],
            'value_ids': [(6, 0, av)]
        }])
        print("Attribute_Line: {}".format(attribute_line))


    i = 0
    for variant in j['variants']:

        attribute_value_ids = []
        for a in variant["attributes"]:
            print("-SKU: {}: Attribute: {}: Value: {}".format(variant["sku"], a["name"], a["value"]))

            attr_id = ab.get_attribute_id(a["name"])
            av_id = ab.get_attribute_value_id(attr_id, a["value"])
            attribute_value_ids.append(av_id)
            print("-AID: {}, AVID:{}".format(attr_id, av_id))

        print("-Attribute Values Array: {}".format(attribute_value_ids))

        if i == 0:
            print("First Variant: {}".format(variant["sku"]))
            # Write the First Variant (created by default)
            models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'write', [[sku1], {
                'default_code': variant['sku'],
                'code': variant['sku'],
                'price': variant['price'],
                'attribute_value_ids': [(6, 0, attribute_value_ids)]
            }])
            sku2 = sku1
        else:
            print("Next Variant: {}".format(variant["sku"]))
            sku2 = models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'create', [{
                'default_code': variant['sku'],
                'code': variant['sku'],
                'price': variant['price'],
                'product_tmpl_id': prod_tmpl_id,
                'type': 'product',
                # 'attribute_line_id': j['product']['attribute_ids'][0],
                'attribute_value_ids': [(6, 0, attribute_value_ids)]
            }])

        # Create Product SupplierInfo Relationship

        for s in variant["suppliers"]:
            sa = models.execute_kw(o_db, o_uid, o_pw, 'product.supplierinfo', 'create', [{
                'product_code': s['supplier_code'],
                'product_id': sku2,
                'price': s['supplier_cost'],
                'name': s['supplier_odoo_id'],
                'product_tmpl_id': prod_tmpl_id,
                'product_name': s['supplier_product_name'],
                'display_name': s['supplier_name'],
            }])
            print("SupplierInfo:")
            pprint.pprint(sa)

        i += 1




# print("----------------------------------------------------------")
# output = models.execute_kw(o_database, uid, o_password,
#                            'product.template', 'search_read',
#                            [[['id', '=', '838']]],
#                            )
# pprint.pprint(output)
# print("----------------------------------------------------------")
# # output = models.execute_kw(o_database, uid, o_password,
# #                            'product.template', 'search_read',
# #                            [[['id', '=', '842']]],
# #                            )
# # pprint.pprint(output)
# print("----------------------------------------------------------")
# print("Attribute 743:")
# ab.dump_attributes()
# print("----------------------------------------------------------")
# attribute_lines = models.execute_kw(o_database, uid, o_password,
#                            'product.attribute.line', 'search_read',
#                            [],
#                            )
# pprint.pprint(attribute_lines)
# for al in attribute_lines:
#     print("attribute_lines (id:{}) display_name:{} attribute_id:{}".format(al["id"], al["display_name"], al["attribute_id"]))



# dump_item_data(o_database, uid, o_password, [[['id','=', '1433']]], 'all')
pprint.pprint(dump_item_data(o_database, uid, o_password, [[['id','=', '1455']]], 'all'))
pprint.pprint(dump_item_data(o_database, uid, o_password, [[['id','=', '1456']]], 'all'))
#
# print("----------------------------------------------------------")
# output = models.execute_kw(o_database, uid, o_password,
#                            'product.supplierinfo', 'search_read',
#                            [],
#                            )
# pprint.pprint(output)
#
# set_inventory_qty(o_database, uid, o_password, 1455, 75, 13)
# set_inventory_qty(o_database, uid, o_password, 1456, 76, 7)
#
#
# print("----------------------------------------------------------")
# output = models.execute_kw(o_database, uid, o_password,
#                            'stock.change.product.qty', 'create',
#                            [{
#                                'location_id': 12,
#                                'product_id': 1455,
#                                'total_quantity': 75.0,
#                                'new_quantity': 75.0,
#                                'quantity': 75.0,
#                                'product_tmpl_id': 899
#                            }]
#                            )
# pprint.pprint(output)
# output = models.execute_kw(o_database, uid, o_password,
#                            'stock.change.product.qty', 'search_read',
#                            [],
#                            )
# pprint.pprint(output)
# fields = {'fields': ['id', 'complete_name', 'display_name', 'location_id', 'name']}
# output = models.execute_kw(o_database, uid, o_password,
#                            'stock.location', 'search_read',
#                            [],
#                            fields)
# pprint.pprint(output)

for product in mjps["products"]:
    build_odoo_product_from_json_multi(o_database, uid, o_password, product)
