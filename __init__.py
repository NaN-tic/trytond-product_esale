#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .menu import *
from .product import *

def register():
    Pool.register(
        CatalogMenu,
        Template,
        ProductMenu,
        ProductRelated,
        ProductUpSell,
        ProductCrossSell,
        module='product_esale', type_='model')

