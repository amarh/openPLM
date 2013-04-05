from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from openPLM.plmapp.utils import memoize_noarg

from .plmobject import (PLMObject, get_all_subclasses,
        get_all_subclasses_with_level, PLMObjectQuerySet, PLMObjectManager)

# parts stuff

class PartQuerySet(PLMObjectQuerySet):
    """
    A :class:`.PLMObjectQuerySet` with extra methods to annotate results
    with the number of children or parents.
    """

    def with_children_counts(self):
        """
        Annotates results with the number of children (field ``num_children``).
        """
        return self.extra(select={"num_children" :
"""
SELECT COUNT(plmapp_parentchildlink.id) from plmapp_parentchildlink
    WHERE plmapp_parentchildlink.end_time IS NULL AND
    plmapp_parentchildlink.parent_id = plmapp_part.plmobject_ptr_id
"""})

    def with_parents_counts(self):
        """
        Annotates results with the number of parents (field ``num_parents``).
        """
        return self.extra(select={"num_parents" :
"""
SELECT COUNT(plmapp_parentchildlink.id) from plmapp_parentchildlink
    WHERE plmapp_parentchildlink.end_time IS NULL AND
    plmapp_parentchildlink.child_id = plmapp_part.plmobject_ptr_id
"""})


class PartManager(PLMObjectManager):
    """
    Manager for :class:`Part`. Uses a :class:`PartQuerySet`.
    """

    use_for_related_fields = True

    def get_query_set(self):
        return PartQuerySet(self.model)

    def with_children_counts(self):
        """
        Shorcut for ``self.get_query_set().with_children_counts()``.
        See :meth:`PartQuerySet.with_children_counts`.
        """
        return self.get_query_set().with_children_counts()

    def with_parents_counts(self):
        """
        Shorcut for ``self.get_query_set().with_parents_counts()``.
        See :meth:`PartQuerySet.with_parents_counts`.
        """
        return self.get_query_set().with_parents_counts()


class TopAssemblyManager(PartManager):
    """
    A :class:`PartManager` that returns only top assemblies.
    A top assemblies is a part with at least one child and no parents.
    """

    def get_query_set(self):
        from openPLM.plmapp.models.link import ParentChildLink
        current_pcl = ParentChildLink.current_objects
        return super(TopAssemblyManager, self).get_query_set().\
                exclude(id__in=current_pcl.values_list("child")).\
                filter(id__in=current_pcl.values_list("parent"))


class AbstractPart(models.Model):
    """
    Abstract model that defines two managers:

    .. attribute:: objects

        default manager, a :class:`.PartManager`

    .. attribute:: top_assemblies:

        a :class:`TopAssemblyManager`
    """
    class Meta:
        abstract = True

    objects = PartManager()
    top_assemblies = TopAssemblyManager()


# first extends AbstractPart to inherit objects
class Part(AbstractPart, PLMObject):
    """
    Model for parts
    """

    class Meta:
        app_label = "plmapp"

    @property
    def menu_items(self):
        items = list(super(Part, self).menu_items)
        items.extend([ugettext_noop("BOM-child"), ugettext_noop("parents"),
                      ugettext_noop("alternates"), ugettext_noop("doc-cad")])
        return items

    def is_promotable(self):
        """
        Returns True if the part is promotable.

        A part is promotable if:

            #. its state is not the last state of its lifecycle

            #. if the part is official.

            #. the part is draft or proposed and:

                #. there is a next state in its lifecycle and if its children
                    which have the same lifecycle are in a state as mature as
                    the object's state.

                #. if the part has no children, there is at least one official
                   document attached to it.
        """
        if not self._is_promotable():
            return False
        if self.is_official:
            return True
        if self.approvals.now().exists():
            # previous signers have already checked if it was promotable
            return True
        from .link import AlternatePartSet
        # check children
        lcs = self.lifecycle.to_states_list()
        rank = lcs.index(self.state.name)
        invalid_states = lcs[:rank + 1]
        invalid_children = list(self.parentchildlink_parent.now().\
                filter(child__lifecycle=self.lifecycle, child__state__in=invalid_states).\
                values_list("child", flat=True))
        if invalid_children:
            # one of their alternate parts may be at the right state
            ps = AlternatePartSet.objects.now().filter(parts__in=invalid_children).distinct()
            alt = dict(Part.objects.filter(alternatepartsets__in=ps).
                    extra(select={"psid":"alternatepartset_id"}).values_list("id", "psid"))
            if alt:
                valid_alternates = Part.objects.filter(id__in=alt.keys(),
                        lifecycle=self.lifecycle).exclude(state__in=invalid_states)
                valid_alternates = set(valid_alternates.values_list("id", flat=True))
                valid_partsets = set(s for p, s in alt.iteritems() if p in valid_alternates)
                valid = all(alt.get(child) in valid_partsets for child in invalid_children)
            else:
                valid = False
            if not valid:
                self._promotion_errors.append(_("Some children are at a lower or draft state."))
            return valid
        if self.is_draft and not self.parentchildlink_parent.now().exists():
            # check that at least one document is attached and its state is official
            # see ticket #57
            links = self.documentpartlink_part.now().filter(document__state=F("document__lifecycle__official_state"))
            found = links.exists()
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
    level="=>"
    get_all_subclasses_with_level(Part, lst , level)
    return lst


