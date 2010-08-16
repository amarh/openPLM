from django import forms
class FakeItems(object):
    def __init__(self, values):
        self.values = values
    
    def items(self):
        return self.values

# example
Form = type("ppp", (forms.BaseForm,), {"base_fields" : FakeItems( [("e", forms.CharField()), ("a", forms.CharField()), ("t", forms.IntegerField())] )})

# possible values from a list of field names
# values = [(name, fields_dict[name]) for name in sorted_list]


