#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from .tools import slugify

__all__ = ['Template', 'ProductMenu', 'ProductRelated', 'ProductUpSell',
    'ProductCrossSell',]
__metaclass__ = PoolMeta


class Template:
    __name__ = 'product.template'
    esale_available = fields.Boolean('Available eSale',
            states={
                'readonly': Eval('esale_available', True),
            },
            help='This product are available in your e-commerce. ' \
            'If you need not publish this product (despublish), ' \
            'unmark Active field in eSale section.')
    esale_active = fields.Boolean('Active')
    esale_visibility = fields.Selection([
            ('all','All'),
            ('search','Search'),
            ('catalog','Catalog'),
            ('none','None'),
            ], 'Visibility')
    esale_slug = fields.Char('Slug', translate=True,
            states={
                'required': Eval('esale_available', True),
            },
            on_change_with=['name'],
            depends=['esale_available'])
    esale_shortdescription = fields.Text('Short Description', translate=True)
    esale_description = fields.Text('Sale Description', translate=True)
    esale_metadescription = fields.Char('Meta Description', translate=True,
            help='Almost all search engines recommend it to be shorter ' \
            'than 155 characters of plain text')
    esale_metakeyword = fields.Char('Meta Keyword', translate=True)
    esale_metatitle = fields.Char('Meta Title', translate=True)
    esale_menus = fields.Many2Many('product.template-esale.catalog.menu',
            'template', 'menu', 'Menus')
    esale_relateds = fields.Many2Many('product.template-product.related', 
            'template', 'related', 'Relateds',
            domain=[
                ('id', '!=', Eval('id')),
                ('esale_available', '=', True),
                ('salable', '=', True),
            ], depends=['id'])
    esale_upsells = fields.Many2Many('product.template-product.upsell',
            'template', 'upsell', 'Up Sells',
            domain=[
                ('id', '!=', Eval('id')),
                ('esale_available', '=', True),
                ('salable', '=', True),
            ], depends=['id'])
    esale_crosssells = fields.Many2Many('product.template-product.crosssell',
            'template', 'crosssell', 'Cross Sells',
            domain=[
                ('id', '!=', Eval('id')),
                ('esale_available', '=', True),
                ('salable', '=', True),
            ], depends=['id'])
    esale_sequence = fields.Integer('Sequence', 
            help='Gives the sequence order when displaying category list.')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls._error_messages.update({
            'slug_empty': 'Slug field is empty!',
            'slug_exists': 'Slug %s exists. Get another slug!',
        })

    @staticmethod
    def default_esale_active():
        return True

    @staticmethod
    def default_esale_visibility():
        return 'all'

    def on_change_with_esale_slug(self):
        """Create slug from name: az09"""
        name = self.name or ''
        name = slugify(name)
        return name

    @classmethod
    def get_slug(cls, id, slug, shops):
        """Get another product is same slug
        Slug is identificator unique by shop
        :param id: int
        :param slug: str
        :param shop: obj
        :return True or False
        """
        for shop in shops:
            records = [t.id for t in cls.search([('esale_websites','in',[shop])])]
            if id and id in records:
                records.remove(id)
            products = cls.search([('esale_slug','=',slug),('id','in',records)])
            if len(products)>0:
                cls.raise_user_error('slug_exists', slug)
        return True

    @classmethod
    def create(cls, vlist):
        for values in vlist:
            values = values.copy()
            if values.get('esale_available'):
                shops = []
                slug = values.get('esale_slug')
                if not slug:
                    cls.raise_user_error('slug_empty')
                for s in values.get('esale_websites'):
                    if s[0] == 'add':
                        shops = s[1]
                cls.get_slug(None, slug, shops)
        return super(Template, cls).create(vlist)

    @classmethod
    def write(cls, products, values):
        """Get another product slug same shop"""
        values = values.copy()
        for product in products:
            slug = values.get('esale_slug')
            esale_websites = values.get('esale_websites')
            if slug or esale_websites:
                shops = []
                if not slug:
                    slug = product.esale_slug
                if esale_websites:
                    for s in esale_websites:
                        if s[0] == 'add':
                            shops = s[1]
                else:
                    shops = [x.id for x in product.esale_websites]
                cls.get_slug(id, slug, shops)
        return super(Template, cls).write(products, values)


class ProductMenu(ModelSQL):
    'Product - Menu'
    __name__ = 'product.template-esale.catalog.menu'
    _table = 'product_template_esale_catalog_menu'

    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            select=True, required=True)
    menu = fields.Many2One('esale.catalog.menu', 'Menu', ondelete='CASCADE',
            select=True, required=True)


class ProductRelated(ModelSQL):
    'Product - Related'
    __name__ = 'product.template-product.related'
    _table = 'product_template_product_related'

    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            select=True, required=True)
    related = fields.Many2One('product.template', 'Related', ondelete='CASCADE',
            select=True, required=True)


class ProductUpSell(ModelSQL):
    'Product - Upsell'
    __name__ = 'product.template-product.upsell'
    _table = 'product_template_product_upsell'

    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            select=True, required=True)
    upsell = fields.Many2One('product.template', 'Upsell', ondelete='CASCADE',
            select=True, required=True)


class ProductCrossSell(ModelSQL):
    'Product - Cross Sell'
    __name__ = 'product.template-product.crosssell'
    _table = 'product_template_product_crosssell'
    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            select=True, required=True)
    crosssell = fields.Many2One('product.template', 'Cross Sell', ondelete='CASCADE',
            select=True, required=True)
