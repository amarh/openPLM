from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from openPLM.plmapp.utils import memoize_noarg

from .plmobject import (PLMObject, get_all_subclasses,
        get_all_subclasses_with_level)

# parts stuff

class Part(PLMObject):
    """
    Model for parts
    """

    class Meta:
        app_label = "plmapp"

    @property
    def menu_items(self):
        items = list(super(Part, self).menu_items)
        items.extend([ugettext_noop("BOM-child"), ugettext_noop("parents"), 
                      ugettext_noop("doc-cad")])
        return items

    def is_promotable(self):
        """
        Returns True if the part is promotable. 
        
        A part is promotable if:
            
            #. its state is not the last state of its lifecycle
            
            #. if the part is not editable (its state is official).
            
            #. the part is editable and:

                #. there is a next state in its lifecycle and if its children
                    which have the same lifecycle are in a state as mature as
                    the object's state.  

                #. if the part has no children, there is at least one official
                   document attached to it.
        """
        if not self._is_promotable():
            return False
        if not self.is_editable:
            return True
        # check children
        children = self.parentchildlink_parent.filter(end_time__exact=None).only("child")
        lcs = self.lifecycle.to_states_list()
        rank = lcs.index(self.state.name)
        for link in children:
            child = link.child
            if child.lifecycle == self.lifecycle:
                rank_c = lcs.index(child.state.name)
                if rank_c == 0 or rank_c < rank:
                    self._promotion_errors.append(_("Some children are at a lower or draft state."))
                    return False
        if not children:
            # check that at least one document is attached and its state is official
            # see ticket #57
            found = False
            links = self.documentpartlink_part.all()
            for link in links:
                found = link.document.is_official
                if found:
                    break
            if not found:
                self._promotion_errors.append(_("There are no official documents attached."))
            return found
        return True

    @property
    def is_part(self):
        return True
    
    @property
    def is_document(self):
        return False


@memoize_noarg
def get_all_parts():
    u"""
    Returns a dict<part_name, part_class> of all available :class:`.Part` classes
    """
    res = {}
    get_all_subclasses(Part, res)
    return res

@memoize_noarg
def get_all_parts_with_level():
    lst = []
    level=">"
    get_all_subclasses_with_level(Part, lst , level)
    return lst   


