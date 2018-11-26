from xmlrpc.client import ServerProxy
import yaml
import sys
import pprint



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
common = ServerProxy('https://{}/xmlrpc/2/common'.format(o_hostname))
# print("Version: {}".format(common.version()))

# Login seems to do the same as authenticate (below).
# uid = common.login(o_database, o_username, o_password)

uid = common.authenticate(o_database, o_username, o_password, {})
# print("authenticate: usermane={}, password={}, UID: {}".format(o_username, o_password, uid))
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

# sku_id = get_id_by_sku(o_database, uid, o_password, 'F-MIRR-CARA')
# print("SKU ID: {}".format(sku_id))

# This is the example JSON I want to build:
pj = {
    'product': {
        'id': 12345,
        'type': 'product',
        'name': 'Nagoya Nightstand',
        'attribute_ids': [1],               # Finish
        'attribute_value_ids': [1, 2, 4],      # Caramelized, Sable, Dark Walnut
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
            },
            {
                'code': 'F-NS-DWAL',
                'type': 'product',
                'attribute_ids': [1],
                'attribute_value_ids': [4]
            }

        ]
    }
}

# print("Product: {}".format(pj['product']['id']))
# print("SKU 1: {}".format(pj['product']['variants'][0]['code']))
# print("SKU 2: {}".format(pj['product']['variants'][1]['code']))
# print("SKU 2: {}".format(pj['product']['variants'][2]['code']))


def build_odoo_product_from_json(o_db, o_uid, o_pw, j):
    print("Building Odoo Product from JSON")

    # Create the "Product" via the Product.Template
    prod_tmpl_id = models.execute_kw(o_db, o_uid, o_pw, 'product.template', 'create', [{
        'name': j['product']['name'],
        'type': j['product']['type'],
        'attribute_line_id': j['product']['attribute_ids'][0],
        'attribute_value_ids': [(6, 0, j['product']['variants'][0]['attribute_value_ids'][0])]
    }])
    print("Product Template ID: {}".format(prod_tmpl_id))

    # Create Product Attributes
    attribute_line = models.execute_kw(o_db, o_uid, o_pw, 'product.attribute.line', 'create', [{
        'product_tmpl_id': int(prod_tmpl_id),
        'attribute_id': j['product']['attribute_ids'][0],
        'value_ids': [(6, 0, j['product']['attribute_value_ids'])]
    }])
    print("Attribute_Line: {}".format(attribute_line))

    # Get the Product ID Created by the Template
    sku_output = models.execute_kw(o_db, o_uid, o_pw, 'product.template', 'search_read',
                                   [[['id', '=', prod_tmpl_id]]],
                                   {'fields': ['product_variant_ids']}
                                   )
    sku1 = sku_output[0]['product_variant_ids'][0]

    i = 0
    for variant in j['product']['variants']:

        if i == 0:
            # Write the First Variant (created by default)
            models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'write', [[sku1], {
                'default_code': variant['code'],
                'code': variant['code'],
                'attribute_value_ids': [(6, 0, variant['attribute_value_ids'])]
            }])
        else:
            models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'create', [{
                'default_code': variant['code'],
                'code': variant['code'],
                'product_tmpl_id': prod_tmpl_id,
                'type': 'product',
                'attribute_line_id': j['product']['attribute_ids'][0],
                'attribute_value_ids': [(6, 0, variant['attribute_value_ids'])]
            }])

        i += 1

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

mjps = {
   "products":[
      {
         "id":"718",
         "name":"Arata Platform Bed",
         "prod_id":"1003",
         "type":"product",
         "variants":[
            {
               "sku":"F-ARA-K-WE/WH",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Wenge/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-CK-WE/PG",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"California King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Wenge/Pearl Grey"
                  }
               ]
            },
            {
               "sku":"F-ARA-Q-WA/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"Queen"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Walunt/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-K-GO/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Grey Oak/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-Q-WE/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"Queen"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Wenge/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-K-WE/PG",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Wenge/Pearl Grey"
                  }
               ]
            },
            {
               "sku":"F-ARA-CK-WA/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"California King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Walunt/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-Q-GO/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"Queen"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Grey Oak/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-CK-WE/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"California King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Wenge/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-Q-WE/PG",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"Queen"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Wenge/Pearl Grey"
                  }
               ]
            },
            {
               "sku":"F-ARA-K-WA/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Walunt/White"
                  }
               ]
            },
            {
               "sku":"F-ARA-CK-GO/WH",
               "type":"product",
               "attributes":[
                  {
                     "id":"138",
                     "name":"Mattress Size",
                     "value":"California King"
                  },
                  {
                     "id":"93",
                     "name":"Color",
                     "value":"Grey Oak/White"
                  }
               ]
            }
         ],
         "attribute_ids":[
            {
               "id":"138",
               "name":"Mattress Size"
            },
            {
               "id":"93",
               "name":"Color",

            }
         ],
         "attribute_value_ids":[
            {
               "value":"King"
            },
            {
               "value":"California King"
            },
            {
               "value":"Queen"
            }
         ]
      }
   ]
}






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
                'attribute_value_ids': [(6, 0, attribute_value_ids)]
            }])
        else:
            print("Next Variant: {}".format(variant["sku"]))
            sku2 = models.execute_kw(o_db, o_uid, o_pw, 'product.product', 'create', [{
                'default_code': variant['sku'],
                'code': variant['sku'],
                'product_tmpl_id': prod_tmpl_id,
                'type': 'product',
                # 'attribute_line_id': j['product']['attribute_ids'][0],
                'attribute_value_ids': [(6, 0, attribute_value_ids)]
            }])

        i += 1


for product in mjps["products"]:
    ''''''
    build_odoo_product_from_json_multi(o_database, uid, o_password, product)
    # print("Product: {}".format(product))

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

