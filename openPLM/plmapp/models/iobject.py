class IObject(object):

    @property
    def title(self):
        return ""

    @property
    def plmobject_url(self):
        return u""

    @property
    def menu_items(self):
        "menu items to choose a view"
        return []

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return []

    @classmethod
    def get_creation_fields(cls):
        """
        Returns fields which should be displayed in a creation form.
        """
        return []

    @classmethod
    def get_modification_fields(cls):
        """
        Returns fields which should be displayed in a modification form
        """
        return []

