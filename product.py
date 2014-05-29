#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from .tools import slugify

__all__ = ['Template', 'Product', 'ProductMenu', 'ProductRelated',
    'ProductUpSell', 'ProductCrossSell',]
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
            depends=['esale_available'])
    esale_shortdescription = fields.Text('Short Description', translate=True,
        help='You could write wiki markup to create html content. Formats text following '
        'the MediaWiki (http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    esale_description = fields.Text('Sale Description', translate=True,
        help='You could write wiki markup to create html content. Formats text following '
        'the MediaWiki (http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
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
    esale_images = fields.Function(fields.Char('eSale Images'), 'get_esale_images')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls._error_messages.update({
            'slug_empty': 'Slug field is empty!',
            'slug_exists': 'Slug %s exists. Get another slug!',
            'delete_esale_template': 'Product %s is esale active. '
                'Descheck active field to dissable esale products',
        })

    @staticmethod
    def default_esale_active():
        return True

    @staticmethod
    def default_esale_visibility():
        return 'all'

    @fields.depends('name')
    def on_change_with_esale_slug(self):
        """Create slug from name: az09"""
        name = self.name or ''
        name = slugify(name)
        return name

    @classmethod
    def get_slug(cls, id, slug):
        """Get another product is same slug
        Slug is identificator unique
        :param id: int
        :param slug: str
        :return True or False
        """
        Config = Pool().get('sale.configuration')
        config = Config(1)
        if not config.check_slug:
            return True

        records = [t.id for t in cls.search([('esale_available','=', True)])]
        if id and id in records:
            records.remove(id)
        products = cls.search([('esale_slug','=',slug),('id','in',records)])
        if products:
            cls.raise_user_error('slug_exists', slug)
        return True

    def get_esale_images(self, name):
        '''Return dict product images: base, small and thumb'''
        images = {}
        base = None
        small = None
        thumb = None
        for attachment in self.attachments:
            if not attachment.esale_available or attachment.esale_exclude:
                continue 
            if attachment.esale_base_image and not base:
                base = attachment.name
            if attachment.esale_small_image and not small:
                small = attachment.name
            if attachment.esale_thumbnail and not thumb:
                thumb = attachment.name

        images['base'] = base
        images['small'] = small
        images['thumbnail'] = thumb

        return images

    @classmethod
    def create(cls, vlist):
        for values in vlist:
            values = values.copy()
            if values.get('esale_available'):
                slug = values.get('esale_slug')
                if not slug:
                    cls.raise_user_error('slug_empty')
                cls.get_slug(None, slug)
        return super(Template, cls).create(vlist)

    @classmethod
    def write(cls, *args):
        """Get another product slug same shop"""
        actions = iter(args)
        for templates, values in zip(actions, actions):
            slug = values.get('esale_slug')
            esale_websites = values.get('esale_websites')
            if slug or esale_websites:
                for template in templates:
                    if not slug:
                        slug = template.esale_slug
                    cls.get_slug(template.id, slug)
        return super(Template, cls).write(templates, *args)

    @classmethod
    def copy(cls, templates, default=None):
        new_templates = []
        for template in templates:
            if template.esale_slug:
                default['esale_slug'] = '%s-copy' % template.esale_slug
            new_template, = super(Template, cls).copy([template], default=default)
            new_templates.append(new_template)
        return new_templates

    @classmethod
    def delete(cls, templates):
        for template in templates:
            if template.esale_available:
                cls.raise_user_error('delete_esale_template', (template.rec_name,))
        super(Template, cls).delete(templates)


class Product:
    __name__ = 'product.product'

    @classmethod
    def get_product_relateds(cls, products, exclude=False):
        '''
        Products Relateds.
        Exclude option: not return related product if are in products
        :param products: object list
        :param exclude: bool
        Return list dict product, price
        '''
        prods = []
        templates = []
        relateds = []

        if not products:
            return None

        for product in products:
            templates.append(product.template)
            if product.esale_relateds:
                for template in product.esale_relateds:
                    relateds.append(template)

        if not relateds:
            return None

        relateds = list(set(relateds))
        if exclude:
            relateds = list(set(relateds) - set(templates))
        prices = cls.get_sale_price(relateds, 1)
        for template in relateds:
            product, = template.products
            prods.append({
                'product': product,
                'unit_price': prices[product.id],
                })
        return prods

    @classmethod
    def get_product_upsells(cls, products, exclude=False):
        '''
        Products Up Sells
        Exclude option: not return upsell product if are in products
        :param products: object list
        :param exclude: bool
        Return list dict product, price
        '''
        prods = []
        templates = []
        upsells = []

        if not products:
            return None

        for product in products:
            templates.append(product.template)
            if product.esale_upsells:
                for template in product.esale_upsells:
                    upsells.append(template)

        if not upsells:
            return None

        upsells = list(set(upsells))
        if exclude:
            upsells = list(set(upsells) - set(templates))
        prices = cls.get_sale_price(upsells, 1)
        for template in upsells:
            product, = template.products
            prods.append({
                'product': product,
                'unit_price': prices[product.id],
                })
        return prods

    @classmethod
    def get_product_crosssells(cls, products, exclude=False):
        '''
        Products Crosssells
        Exclude option: not return upsell product if are in products
        :param products: object list
        :param exclude: bool
        Return list dict product, price
        '''
        prods = []
        templates = []
        crosssells = []

        if not products:
            return None

        for product in products:
            templates.append(product.template)
            if product.esale_crosssells:
                for template in product.esale_crosssells:
                    crosssells.append(template)

        if not crosssells:
            return None

        crosssells = list(set(crosssells))
        if exclude:
            crosssells = list(set(crosssells) - set(templates))
        prices = cls.get_sale_price(crosssells, 1)
        for template in crosssells:
            product, = template.products
            prods.append({
                'product': product,
                'unit_price': prices[product.id],
                })
        return prods


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
