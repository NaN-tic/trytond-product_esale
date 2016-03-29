# This file is part product_esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Configuration']


class Configuration:
    __metaclass__ = PoolMeta
    __name__ = 'product.configuration'
    template_attribute_set = fields.Property(fields.Many2One('product.attribute.set',
            'Template Attribute Set'))
    template_attribute_set_options = fields.Property(fields.Char(
            'Template Attribute Set Options',
            help='Default attribute options when create new product:\n' \
                'key:value|key2:value2'))
    product_attribute_set = fields.Property(fields.Many2One('product.attribute.set',
            'Product Attribute Set'))
    product_attribute_set_options = fields.Property(fields.Char(
            'Product Attribute Set Options',
            help='Default attribute options when create new product:\n' \
                'key:value|key2:value2'))
    default_uom = fields.Property(fields.Many2One('product.uom',
            'Default UOM'))
    check_slug = fields.Boolean('Check Slug',
        help='Check slug exist in products and menus')

    @staticmethod
    def default_check_slug():
        return True
