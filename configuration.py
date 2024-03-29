# This file is part product_esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.modules.company.model import CompanyValueMixin

attribute_set = fields.Many2One('product.attribute.set',
    'Template Attribute Set')
attribute_set_options = fields.Char('Template Attribute Set Options',
    help=('Default attribute options when create new product:\n'
        'key:value|key2:value2'))
default_uom = fields.Many2One('product.uom', 'Default UOM')


class Configuration(metaclass=PoolMeta):
    __name__ = 'product.configuration'
    default_uom = fields.MultiValue(default_uom)
    check_slug = fields.Boolean('Check Slug',
        help='Check slug exist in products and menus')

    @staticmethod
    def default_check_slug():
        return True

    @classmethod
    def multivalue_model(cls, field):
        if field in ['default_uom']:
            return Pool().get('sale.configuration.product.esale')
        return super().multivalue_model(field)


class ConfigurationProductESale(ModelSQL, CompanyValueMixin):
    "Product eSale Configuration Company Values"
    __name__ = 'sale.configuration.product.esale'
    default_uom = default_uom


class ConfigurationAttribute(metaclass=PoolMeta):
    __name__ = 'product.configuration'
    attribute_set = fields.MultiValue(attribute_set)
    attribute_set_options = fields.MultiValue(
            attribute_set_options)

    @classmethod
    def multivalue_model(cls, field):
        if field in ['attribute_set', 'attribute_set_options']:
            return Pool().get('sale.configuration.product.esale')
        return super().multivalue_model(field)


class ConfigurationProductESaleAttribute(metaclass=PoolMeta):
    __name__ = 'sale.configuration.product.esale'
    attribute_set = attribute_set
    attribute_set_options = attribute_set_options
