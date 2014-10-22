#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Configuration']
__metaclass__ = PoolMeta


class Configuration:
    __name__ = 'product.configuration'
    template_attribute_set = fields.Property(fields.Many2One('product.attribute.set',
            'Template Attribute Set'))
    product_attribute_set = fields.Property(fields.Many2One('product.attribute.set',
            'Product Attribute Set'))
    default_uom = fields.Property(fields.Many2One('product.uom',
            'Default UOM'))
    check_slug = fields.Boolean('Check Slug',
        help='Check slug exist in products and menus')

    @staticmethod
    def default_check_slug():
        return True
