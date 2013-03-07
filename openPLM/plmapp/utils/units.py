u"""
This module defines two constants:

.. data:: DEFAULT_UNIT

    The default unit of a BOM row: ``-`` (each)

.. data:: UNITS

    All valid units of a BOM row.
"""

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

class UnitConversionError(Exception):
    """
    .. versionadded:: 1.1

    Exception raised if an error occurs while converting
    a value from one unit to another one.
    """
    pass

FACTORS = {

    'mm' : (0.001, 'm'),
    'cm' : (0.01, 'm'),
    'dm' : (0.1, 'm'),
    'm' : (1., 'm'),
    'km' : (1000, 'm'),

    'mg' : (0.001, 'g'),
    'cg' : (0.01, 'g'),
    'dg' : (0.1, 'g'),
    'g' : (1., 'g'),
    'kg' : (1000, 'g'),

    'mol' : (6.0221404e23, '-'),
    '-' : (1., '-'),

    'm3' : (1000., 'L'),
    'mL' : (0.001, 'L'),
    'cL' : (0.01, 'L'),
    'dL' : (0.1, 'L'),
    'L' : (1., 'L'),
    }

def convert_unit(value, original_unit, new_unit):
    """
    .. versionadded:: 1.1

    Converts a value expressed in *original_unit* to
    *new_unit*

    :raises: :exc:`UnitConversionError` if the conversion is not possible.

    Here is an example :

        >>> convert_unit(1, 'm', 'mm')
        1000.0
        >>> convert_unit(5, 'dm', 'mm')
        500.0
        >>> convert_unit(5, 'dL', 'm3')
        0.00050000000000000001
        >>> convert_unit(5, 'dL', 'kg')
        ------------------------------------------------------------
        Traceback (most recent call last):
          File "<ipython console>", line 1, in <module>
          File plmpapp/utils/units.py", line 80, in convert_unit
            def convert_unit(value, original_unit, new_unit):
        UnitConversionError: Inconsistent units (dL, kg)
    """
    factor1, base1 = FACTORS[original_unit]
    factor2, base2 = FACTORS[new_unit]
    if base1 != base2:
        raise UnitConversionError("Inconsistent units (%s, %s)" % (original_unit, new_unit))
    return value * factor1 / factor2

