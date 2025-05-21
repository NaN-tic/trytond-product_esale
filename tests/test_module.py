
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


class ProductEsaleTestCase(CompanyTestMixin, ModuleTestCase):
    'Test ProductEsale module'
    module = 'product_esale'
    extras = ['product_review', 'product_template_attribute', 'purchase']

    @with_transaction()
    def test_slugify(self):
        'Test slugify'
        pool = Pool()
        Template = pool.get('product.template')
        CatalogMenu = pool.get('esale.catalog.menu')

        template = Template()
        template.name = 'Product Demo'
        template.esale_slug = None
        template.on_change_name()
        self.assertEqual(template.esale_slug, 'product-demo')
        template.esale_slug = 'New Product Demo'
        template.on_change_esale_slug()
        self.assertEqual(template.esale_slug, 'new-product-demo')

        menu = CatalogMenu()
        menu.name = 'Menu Demo'
        menu.slug = None
        menu.on_change_name()
        self.assertEqual(menu.slug, 'menu-demo')

del ModuleTestCase
