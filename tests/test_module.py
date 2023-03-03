
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase


class ProductEsaleTestCase(CompanyTestMixin, ModuleTestCase):
    'Test ProductEsale module'
    module = 'product_esale'
    extras = ['product_review', 'product_template_attribute', 'purchase']


del ModuleTestCase
