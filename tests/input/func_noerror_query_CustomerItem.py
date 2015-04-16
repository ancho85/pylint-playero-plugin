from OpenOrange import *

ParentCustomerItem = SuperClass("CustomerItem", "Record", __file__)
class CustomerItem(ParentCustomerItem):

    def checkCustomerItem(self):
        query = Query()
        query.sql = "SELECT * FROM [Alotment] WHERE {internalId} = s|%s|" % self.internalId
        return query.open()
