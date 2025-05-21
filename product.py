# This file is part product_esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.tools import cursor_dict
from trytond.transaction import Transaction
from trytond.cache import Cache
from trytond.pyson import Eval, Bool
from trytond.tools import slugify
from trytond.i18n import gettext
from trytond.exceptions import UserError

IMAGE_TYPES = ['image/jpeg', 'image/png',  'image/gif']
STATES = {
    'readonly': ~Eval('active', True),
    'invisible': (~Eval('unique_variant', False) & Eval(
        '_parent_template', {}).get('unique_variant', False)),
    }
DEPENDS = ['active', 'unique_variant']

def attribute2dict(s):
    d = {}
    for v in s.split('|'):
        k, v = v.split(':')
        d[k] = v
    return d

def _slugify(value):
    return slugify(value).lower()


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'
    esale_visibility = fields.Selection([
            ('all','All'),
            ('search','Search'),
            ('catalog','Catalog'),
            ('none','None'),
            ], 'Visibility')
    esale_slug = fields.Char('Slug', translate=True,
            states={
                'required': Eval('esale_available', True),
            })
    esale_slug_langs = fields.Function(fields.Dict(None, 'Slug Langs'), 'get_esale_slug_langs')
    esale_shortdescription = fields.Text('Short Description', translate=True,
        help='You could write wiki markup to create html content. Formats text following '
        'the Creole syntax https://en.wikipedia.org/wiki/Creole_(markup)')
    esale_description = fields.Text('Sale Description', translate=True,
        help='You could write wiki markup to create html content. Formats text following '
        'the Creole syntax https://en.wikipedia.org/wiki/Creole_(markup).')
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
                ('id', '!=', Eval('id', -1)),
                ('esale_available', '=', True),
                ('salable', '=', True),
            ])
    esale_upsells = fields.Many2Many('product.template-product.upsell',
            'template', 'upsell', 'Up Sells',
            domain=[
                ('id', '!=', Eval('id', -1)),
                ('esale_available', '=', True),
                ('salable', '=', True),
            ])
    esale_crosssells = fields.Many2Many('product.template-product.crosssell',
            'template', 'crosssell', 'Cross Sells',
            domain=[
                ('id', '!=', Eval('id', -1)),
                ('esale_available', '=', True),
                ('salable', '=', True),
            ])
    esale_sequence = fields.Integer('Sequence',
            help='Gives the sequence order when displaying category list.')
    esale_images = fields.Function(fields.Char('eSale Images'), 'get_esale_images')
    esale_default_images = fields.Function(fields.Char('eSale Default Images'), 'get_esale_default_images')
    esale_all_images = fields.Function(fields.Char('eSale All Images'), 'get_esale_all_images')
    _esale_slug_langs_cache = Cache('product_template.esale_slug_langs')

    @staticmethod
    def default_esale_visibility():
        return 'all'

    @staticmethod
    def default_esale_sequence():
        return 1

    @staticmethod
    def default_default_uom():
        '''Default UOM'''
        Config = Pool().get('product.configuration')
        config = Config(1)
        return config.default_uom.id if config.default_uom else None

    @fields.depends('name', 'esale_slug')
    def on_change_esale_available(self):
        try:
            super(Template, self).on_change_esale_available()
        except AttributeError:
            pass
        if self.name and not self.esale_slug:
            self.esale_slug = _slugify(self.name)

    @fields.depends('name', 'esale_slug')
    def on_change_name(self):
        try:
            super(Template, self).on_change_name()
        except AttributeError:
            pass
        if self.name and not self.esale_slug:
            self.esale_slug = _slugify(self.name)

    @fields.depends('esale_slug')
    def on_change_esale_slug(self):
        if self.esale_slug:
            self.esale_slug = _slugify(self.esale_slug)

    @classmethod
    def view_attributes(cls):
        return super(Template, cls).view_attributes() + [
            ('//page[@id="attachments"]', 'states', {
                    'invisible': Bool(Eval('unique_variant', True)),
                    })]

    @classmethod
    def get_slug(cls, id, slug):
        """Get another product is same slug
        Slug is identificator unique
        :param id: int
        :param slug: str
        :return True or False
        """
        Config = Pool().get('product.configuration')
        config = Config(1)
        if not config.check_slug:
            return True

        records = [t.id for t in cls.search([('esale_available','=', True)])]
        if id and id in records:
            records.remove(id)
        products = cls.search([('esale_slug','=',slug),('id','in',records)])
        if products:
            raise UserError(gettext('product_esale.eslug_exists', slug=slug))
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

    def get_esale_all_images(self, name):
        '''Return list product images'''
        images = []
        for attachment in self.attachments:
            if not attachment.esale_available or attachment.esale_exclude:
                continue
            images.append({
                'name': attachment.name,
                'digest': attachment.file_id,
                })

        return images

    def get_esale_default_images(self, name):
        '''Return dict product digest images: base, small and thumb'''
        images = {}
        base = None
        small = None
        thumb = None
        for attachment in self.attachments:
            if not attachment.esale_available or attachment.esale_exclude:
                continue
            if attachment.esale_base_image and not base:
                base = {
                    'name': attachment.name,
                    'digest': attachment.file_id,
                    }
            if attachment.esale_small_image and not small:
                small = {
                    'name': attachment.name,
                    'digest': attachment.file_id,
                    }
            if attachment.esale_thumbnail and not thumb:
                thumb = {
                    'name': attachment.name,
                    'digest': attachment.file_id,
                    }
        images['base'] = base
        images['small'] = small
        images['thumbnail'] = thumb

        return images

    def get_esale_slug_langs(self, name):
        '''Return dict slugs by all languaes actives'''
        pool = Pool()
        Lang = pool.get('ir.lang')
        Template = pool.get('product.template')

        template_id = self.id
        langs = Lang.search([
            ('active', '=', True),
            ('translatable', '=', True),
            ])

        slugs = {}
        for lang in langs:
            with Transaction().set_context(language=lang.code):
                template, = Template.read([template_id], ['esale_slug'])
                slugs[lang.code] = template['esale_slug']

        return slugs

    @classmethod
    def create(cls, vlist):
        vlist = [v.copy() for v in vlist]
        for values in vlist:
            if values.get('esale_available'):
                name = values.get('name')
                slug = _slugify(values.get('esale_slug', name))
                cls.get_slug(None, slug)
                values['esale_slug'] = slug
        return super(Template, cls).create(vlist)

    @classmethod
    def write(cls, *args):
        """Get another product slug same shop"""
        actions = iter(args)
        args = []
        for templates, values in zip(actions, actions):
            if values.get('esale_slug'):
                slug = _slugify(values.get('esale_slug'))
                for template in templates:
                    cls.get_slug(template.id, slug)
                values['esale_slug'] = slug
            salable = values.get('salable')
            if salable == False:
                values['esale_active'] = False
            args.extend((templates, values))
        return super(Template, cls).write(*args)

    @classmethod
    def copy(cls, templates, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        # by default desactive esale product and slug to None
        default.setdefault('esale_available', None)
        default.setdefault('esale_active', None)
        default.setdefault('esale_slug', None)
        return super(Template, cls).copy(templates, default=default)

    @classmethod
    def delete(cls, templates):
        for template in templates:
            if template.esale_available:
                raise UserError(gettext(
                    'product_esale.delete_esale_template',
                        template=template.rec_name))

        super(Template, cls).delete(templates)

    @staticmethod
    def attribute_options(codes):
        '''Return attribute options convert to dict by code
        @param: names: list
        return dict {'attrname': {options}}
        '''
        options = {}
        cursor = Transaction().connection.cursor()
        names = ["'"+c+"'" for c in codes]
        query = "SELECT name, selection from product_attribute " \
            "where name in (%s) and type_ = 'selection'" % ','.join(names)
        cursor.execute(query)
        vals = cursor_dict(cursor)

        for val in vals:
            opts = {}
            for o in val['selection'].split('\n'):
                opt = o.split(':')
                opts[opt[0]] = opt[1]
            options[val['name']] = opts
        return options


class TemplateAttribute(metaclass=PoolMeta):
    __name__ = 'product.template'

    @staticmethod
    def default_attribute_set():
        '''Product Template Attribute'''
        Config = Pool().get('product.configuration')
        pconfig = Config(1)
        if hasattr(pconfig, 'attribute_set') and pconfig.attribute_set:
            return pconfig.attribute_set.id


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'
    esale_available = fields.Function(fields.Boolean('eSale'),
        'get_esale_available', searcher='search_esale_available')
    esale_active = fields.Function(fields.Boolean('Active eSale'),
        'get_esale_active', searcher='search_esale_active')
    esale_slug = fields.Char('Slug', translate=True, states=STATES)
    esale_sequence = fields.Integer('Sequence',
            help='Gives the sequence order when displaying variants list.')
    unique_variant = fields.Function(fields.Boolean('Unique Variant'),
        'on_change_with_unique_variant')

#     def __getattr__(self, name):
#         result = super(Product, self).__getattr__(name)
#         if not result and name == 'esale_slug':
#             return getattr(self.template, name)
#         return result

    @classmethod
    def __setup__(cls):
        super(Product, cls).__setup__()
        cls._order.insert(0, ('esale_sequence', 'ASC'))

    @staticmethod
    def default_esale_sequence():
        return 1

    @classmethod
    def search(cls, domain, offset=0, limit=None, order=None, count=False,
            query=False):
        for d in domain:
            if d and d[0] == 'esale_slug':
                domain = ['OR', domain[:], ('template.esale_slug', 'ilike', d[2])]
                break
        return super(Product, cls).search(domain, offset=offset, limit=limit,
            order=order, count=count, query=query)

    @fields.depends('template', '_parent_template.unique_variant')
    def on_change_with_unique_variant(self, name=None):
        if self.template:
            return self.template.unique_variant
        return False

    def get_esale_available(self, name):
        return self.template.esale_available if self.template else False

    @classmethod
    def search_esale_available(cls, name, clause):
        return [('template.esale_available',) + tuple(clause[1:])]

    def get_esale_active(self, name):
        return self.template.esale_active if self.template else False

    @classmethod
    def search_esale_active(cls, name, clause):
        return [('template.esale_active',) + tuple(clause[1:])]

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


class ProductAttribute(metaclass=PoolMeta):
    __name__ = 'product.product'

    @staticmethod
    def default_attributes():
        '''Product Attribute Options'''
        Config = Pool().get('product.configuration')
        pconfig = Config(1)
        if (hasattr(pconfig, 'attribute_set_options') and
                pconfig.attribute_set_options):
            return attribute2dict(pconfig.attribute_set_options)


class ProductMenu(ModelSQL):
    'Product - Menu'
    __name__ = 'product.template-esale.catalog.menu'
    _table = 'product_template_esale_catalog_menu'

    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
        required=True)
    menu = fields.Many2One('esale.catalog.menu', 'Menu', ondelete='CASCADE',
        required=True)


class ProductRelated(ModelSQL):
    'Product - Related'
    __name__ = 'product.template-product.related'
    _table = 'product_template_product_related'

    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
        required=True)
    related = fields.Many2One('product.template', 'Related', ondelete='CASCADE',
        required=True)


class ProductUpSell(ModelSQL):
    'Product - Upsell'
    __name__ = 'product.template-product.upsell'
    _table = 'product_template_product_upsell'

    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
        required=True)
    upsell = fields.Many2One('product.template', 'Upsell', ondelete='CASCADE',
        required=True)


class ProductCrossSell(ModelSQL):
    'Product - Cross Sell'
    __name__ = 'product.template-product.crosssell'
    _table = 'product_template_product_crosssell'
    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
        required=True)
    crosssell = fields.Many2One('product.template', 'Cross Sell', ondelete='CASCADE',
        required=True)
