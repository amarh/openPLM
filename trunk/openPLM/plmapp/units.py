from django.utils.translation import ugettext_lazy as _

DEFAULT_UNIT = "-"
UNITS = (
    (_(u'Amounts'), (
        (DEFAULT_UNIT, _(u'Each')),
        ('mol', _(u'mol')),
        )
    ),
    (_(u'Lengths'), (
        ('mm', _(u'mm')),
        ('cm', _(u'cm')),
        ('dm', _(u'dm')),
        ('m', _(u'm')),
        ('km', _(u'km')),
        )
    ),
    (_(u'Volumes'), (
        ('m3', _(u'm\xb3')),
        ('mL', _(u'mL')),
        ('cL', _(u'cL')),
        ('dL', _(u'dL')),
        ('L', _(u'L')),
        )
    ),
    (_(u'Masses'), (
        ('mg', _(u'mg')),
        ('cg', _(u'cg')),
        ('dg', _(u'dg')),
        ('g', _(u'g')),
        ('kg', _(u'kg')),
        )
    ),
)

