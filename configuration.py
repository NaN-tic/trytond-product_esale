# This file is part product_esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond import backend
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.tools.multivalue import migrate_property
from trytond.modules.company.model import CompanyValueMixin

__all__ = ['Configuration', 'ConfigurationProductESale']

template_attribute_set = fields.Many2One('product.attribute.set',
    'Template Attribute Set')
template_attribute_set_options = fields.Char('Template Attribute Set Options',
    help=('Default attribute options when create new product:\n'
        'key:value|key2:value2'))
product_attribute_set = fields.Many2One('product.attribute.set',
    'Product Attribute Set')
product_attribute_set_options = fields.Char('Product Attribute Set Options',
    help=('Default attribute options when create new product:\n'
        'key:value|key2:value2'))
default_uom = fields.Many2One('product.uom', 'Default UOM')


class Configuration(metaclass=PoolMeta):
    __name__ = 'product.configuration'
    template_attribute_set = fields.MultiValue(template_attribute_set)
    template_attribute_set_options = fields.MultiValue(
            template_attribute_set_options)
    product_attribute_set = fields.MultiValue(product_attribute_set)
    product_attribute_set_options = fields.MultiValue(
                        product_attribute_set_options)
    default_uom = fields.MultiValue(default_uom)
    check_slug = fields.Boolean('Check Slug',
        help='Check slug exist in products and menus')

    @staticmethod
    def default_check_slug():
        return True

    @classmethod
    def multivalue_model(cls, field):
        if field in [
                'template_attribute_set',
                'template_attribute_set_options',
                'product_attribute_set',
                'product_attribute_set_options',
                'default_uom',
                ]:
            return Pool().get('sale.configuration.product.esale')
        return super(Configuration, cls).multivalue_model(field)


class ConfigurationProductESale(ModelSQL, CompanyValueMixin):
    "Product eSale Configuration Company Values"
    __name__ = 'sale.configuration.product.esale'
    template_attribute_set = template_attribute_set
    template_attribute_set_options = template_attribute_set_options
    product_attribute_set = product_attribute_set
    product_attribute_set_options = product_attribute_set_options
    default_uom = default_uom

    @classmethod
    def __register__(cls, module_name):
        exist = backend.TableHandler.table_exist(cls._table)

        super(ConfigurationProductESale, cls).__register__(module_name)

        if not exist:
            cls._migrate_property([], [], [])

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.extend([
                'template_attribute_set',
                'template_attribute_set_options',
                'product_attribute_set',
                'product_attribute_set_options',
                'default_uom',
                ])
        value_names.extend([
                'template_attribute_set',
                'template_attribute_set_options',
                'product_attribute_set',
                'product_attribute_set_options',
                'default_uom',
                ])
        migrate_property('sale.configuration', field_names, cls, value_names,
            fields=fields)
