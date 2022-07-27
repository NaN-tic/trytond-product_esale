# This file is part product_esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import attachment
from . import menu
from . import product

def register():
    Pool.register(
        attachment.Attachment,
        menu.CatalogMenu,
        product.Template,
        product.Product,
        product.ProductMenu,
        product.ProductRelated,
        product.ProductUpSell,
        product.ProductCrossSell,
        module='product_esale', type_='model')
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationProductESale,
        module='product_esale', type_='model',
        depends=['product_template_attribute'])
