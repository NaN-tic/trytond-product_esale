#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Configuration']
__metaclass__ = PoolMeta


class Configuration:
    __name__ = 'sale.configuration'
    check_slug = fields.Boolean('Check Slug',
        help='Check slug exist in products and menus')

    @staticmethod
    def default_check_slug():
        return True