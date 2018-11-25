# hello_odoo

This is my "Hello World" experimenting with Odoo's API's.  Also a stash of my notes and learnings from this experiment.

## Notes:
* These experiments are using the Odoo XML-RPC API's.  There are apparently some python or other libraries, including Odoo ORM that you can use to build items in the same way.
* The examples on the Odoo 11 webservices documentation are not Python 3, so you'll have to tweak the default code little to get it to work.  Or just use my code.
* Bitnami Odoo runs on ports 80 and 443, not the default 8069, so keep that in mind.
* Make sure you have xmlrpc available to you.
* It would be way better if there were REST / JSON API's because I'd use my favorite Requests library.
* It seems that XML-RPC is enabled by Default with Odoo on the main port(s).  Check firewall rules, too, if you can't hit them.
* From [here](https://docs.bitnami.com/bch/apps/odoo/administration/add-databases/) the Odoo server configuration file is at /opt/bitnami/apps/odoo/conf/openerp-server.conf and the default database name is bitnami_openerp.


## For starters:
* Create an Odoo instance from Bitnami.
* Create an RPC user (you'll need to log in with the email address)
* Load the accompanying code

## Handy Links:
* [Odoo 11 Webservices Documentation](https://www.odoo.com/documentation/11.0/webservices/odoo.html) - This is most helpful.
* [Jkb's Misc Odoo Notes (internal)](https://docs.google.com/spreadsheets/d/1LrxGuLUhSujMluzCTE8LPBKSwM0tuMNAmZyJnW2c5Xo/edit#gid=0)
* [Bitnami Odoo Stack Readme](https://bitnami.com/stack/odoo/README.txt)
* ^^^ Good stuff referred to most
* [Python 3 XML RPC Reference](https://docs.python.org/release/3.4.2/library/xmlrpc.client.html#module-xmlrpc.client)
* [Odoo new API Guidelines](https://odoo-new-api-guide-line.readthedocs.io/en/latest/) - haven't used these much yet, but it'll probably make more sense with a little more experience.
* Passing Arrays (attributes/values) into XML-RPC API [here](https://www.odoo.com/forum/help-1/question/how-to-create-product-product-variant-using-rpc-101043)
* [PHP Example](https://www.odoo.com/forum/help-1/question/create-product-via-api-88785) adding item to Odoo via XML-RPC
* [Java Example](https://www.odoo.com/fr_FR/forum/aide-1/question/how-to-access-odoo-8-using-java-xmlrpc-83836) for reference
* [Odoo Online XML-RPC Note](https://www.odoo.com/fr_FR/forum/aide-1/question/is-xmlrpc-enabled-on-evaluation-servers-81494)

## TODO:
* ~~Create an item with multiple attributes/variations~~
* Move the Product Creation methods from hello_odoo into a product_builder.py class of some sort.
* Probably move these classes to a models subdirectory, ideally want the test scripts to live in experiments.
* Create a method for pulling the data from a Product (via Product.Template), then see how multi-axis variations looks in the data file.
* Create a method to add a product with multiple axis variations.
* ~~Create attributes and attribute values~~
* ~~Create a class for doing the work versus a ton of functions in hello_odoo.py~~
* ~~Build the JSON format for importing the attributes~~
* Build the JSON format for importing the items
* Save the Import formats into the project
* ~~Import a bunch of data from JSON~~
* Describe the process to test with the JSON data
* Figure out what's up with Odoo ORM and/or the Odoo "high level" openerp (Referenced [here](https://doc.odoo.com/trunk/web/rpc)) Python libraries--is that a thing?
* Review in more detail: [Odoo ORM Page](https://www.odoo.com/documentation/11.0/reference/orm.html)
* Same deal with "low-level" [here](https://doc.odoo.com/trunk/web/rpc#low-level-api-rpc-calls-to-python-side)
* What's the name of the bitnami odoo image?
* What is Odoo "erppeek"?  Referenced [here](https://github.com/Yenthe666/InstallScript/issues/88)
* Maybe split the "Todo" into a deep backlog versus next steps
