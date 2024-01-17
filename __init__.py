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
        configuration.Configuration,
        configuration.ConfigurationProductESale,
        menu.CatalogMenu,
        product.Template,
        product.Product,
        product.ProductMenu,
        product.ProductRelated,
        product.ProductUpSell,
        product.ProductCrossSell,
        module='product_esale', type_='model')
    Pool.register(
        configuration.ConfigurationAttribute,
        configuration.ConfigurationProductESaleAttribute,
        product.TemplateAttribute,
        product.ProductAttribute,
        module='product_esale', type_='model',
        depends=['product_template_attribute'])
