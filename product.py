# This file is part product_esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import os
import hashlib
from mimetypes import guess_type
from PIL import Image
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.cache import Cache
from trytond.pyson import Eval, Bool, Or
from trytond.config import config
from .tools import slugify

__all__ = ['Template', 'Product', 'ProductMenu', 'ProductRelated',
    'ProductUpSell', 'ProductCrossSell',]
__metaclass__ = PoolMeta

IMAGE_TYPES = ['image/jpeg', 'image/png',  'image/gif']
STATES = {
    'readonly': ~Eval('active', True),
    'invisible': (~Eval('unique_variant', False) & Eval(
        '_parent_template', {}).get('unique_variant', False)),
    }
DEPENDS = ['active', 'unique_variant']


class Template:
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
            },
            depends=['esale_available'])
    esale_slug_langs = fields.Function(fields.Dict(None, 'Slug Langs'), 'get_esale_slug_langs')
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
    esale_thumb = fields.Function(fields.Binary('Thumb', filename='esale_thumb_filename',
        help='Thumbnail Product Image'), 'get_esale_thumb', setter='set_esale_thumb')
    esale_thumb_filename = fields.Char('File Name',
        help='Thumbnail Product File Name')
    esale_thumb_path = fields.Function(fields.Char('Thumb Path'), 'get_esale_thumbpath')
    esale_images = fields.Function(fields.Char('eSale Images'), 'get_esale_images')
    esale_default_images = fields.Function(fields.Char('eSale Default Images'), 'get_esale_default_images')
    esale_all_images = fields.Function(fields.Char('eSale All Images'), 'get_esale_all_images')
    _esale_slug_langs_cache = Cache('product_template.esale_slug_langs')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls._error_messages.update({
            'slug_empty': 'Slug field is empty!',
            'slug_exists': 'Slug %s exists. Get another slug!',
            'delete_esale_template': 'Product %s is esale active. '
                'Descheck active field to dissable esale products',
            'not_file_mime': ('Not know file mime "%(file_name)s"'),
            'not_file_mime_image': ('"%(file_name)s" file mime is not an image ' \
                '(jpg, png or gif)'),
            'image_size': ('Thumb "%(file_name)s" size is larger than "%(size)s"Kb'),
        })

    @staticmethod
    def default_esale_visibility():
        return 'all'

    @staticmethod
    def default_esale_sequence():
        return 1

    @staticmethod
    def default_template_attribute_set():
        '''Product Template Attribute'''
        Config = Pool().get('product.configuration')
        config = Config(1)
        if config.template_attribute_set:
            return config.template_attribute_set.id

    @staticmethod
    def default_attribute_set():
        '''Product Attribute'''
        Config = Pool().get('product.configuration')
        config = Config(1)
        if config.product_attribute_set:
            return config.product_attribute_set.id

    @staticmethod
    def default_default_uom():
        '''Default UOM'''
        Config = Pool().get('product.configuration')
        config = Config(1)
        if config.default_uom:
            return config.default_uom.id

    @fields.depends('name', 'esale_slug')
    def on_change_with_esale_slug(self):
        """Create slug from name: az09"""
        if self.esale_slug:
            return self.esale_slug
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
        Config = Pool().get('product.configuration')
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

    def get_esale_all_images(self, name):
        '''Return list product images'''
        images = []
        for attachment in self.attachments:
            if not attachment.esale_available or attachment.esale_exclude:
                continue 
            images.append({
                'name': attachment.name,
                'digest': attachment.digest,
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
                    'digest': attachment.digest,
                    }
            if attachment.esale_small_image and not small:
                small = {
                    'name': attachment.name,
                    'digest': attachment.digest,
                    }
            if attachment.esale_thumbnail and not thumb:
                thumb = {
                    'name': attachment.name,
                    'digest': attachment.digest,
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
        args = []
        for templates, values in zip(actions, actions):
            slug = values.get('esale_slug')
            esale_websites = values.get('esale_websites')
            if slug or esale_websites:
                for template in templates:
                    if not slug:
                        slug = template.esale_slug
                    cls.get_slug(template.id, slug)
            salable = values.get('salable')
            if salable == False:
                values['esale_active'] = False
            args.extend((templates, values))
        return super(Template, cls).write(*args)

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

    @staticmethod
    def attribute_options(codes):
        '''Return attribute options convert to dict by code
        @param: names: list
        return dict {'attrname': {options}}
        '''
        options = {}
        cursor = Transaction().cursor
        names = ["'"+c+"'" for c in codes]
        query = "SELECT name, selection from product_attribute " \
            "where name in (%s) and type_ = 'selection'" % ','.join(names)
        cursor.execute(query)
        vals = cursor.dictfetchall()

        for val in vals:
            opts = {}
            for o in val['selection'].split('\n'):
                opt = o.split(':')
                opts[opt[0]] = opt[1]
            options[val['name']] = opts
        return options

    def get_esale_thumb(self, name):
        db_name = Transaction().cursor.dbname
        filename = self.esale_thumb_filename
        if not filename:
            return None
        filename = os.path.join(config.get('database', 'path'), db_name,
            'esale', 'thumb', filename[0:2], filename[2:4], filename)

        value = None
        try:
            with open(filename, 'rb') as file_p:
                value = buffer(file_p.read())
        except IOError:
            pass
        return value

    def get_esale_thumbpath(self, name):
        filename = self.esale_thumb_filename
        if not filename:
            return None
        return '%s/%s/%s' % (filename[:2], filename[2:4], filename)

    @classmethod
    def set_esale_thumb(cls, templates, name, value):
        if value is None:
            return
        if not value:
            cls.write(templates, {
                'esale_thumb_filename': None,
                })
            return

        Config = Pool().get('product.configuration')
        product_config = Config(1)
        size = product_config.thumb_size or 150

        db_name = Transaction().cursor.dbname
        esaledir = os.path.join(
            config.get('database', 'path'), db_name, 'esale', 'thumb')

        for template in templates:
            file_name = template['esale_thumb_filename']

            file_mime, _ = guess_type(file_name)
            if not file_mime:
                cls.raise_user_error('not_file_mime', {
                        'file_name': file_name,
                        })
            if file_mime not in IMAGE_TYPES:
                cls.raise_user_error('not_file_mime_image', {
                        'file_name': file_name,
                        })

            _, ext = file_mime.split('/')
            digest = '%s.%s' % (hashlib.md5(value).hexdigest(), ext)
            subdir1 = digest[0:2]
            subdir2 = digest[2:4]
            directory = os.path.join(esaledir, subdir1, subdir2)
            filename = os.path.join(directory, digest)

            if not os.path.isdir(directory):
                os.makedirs(directory, 0775)
            os.umask(0022)
            with open(filename, 'wb') as file_p:
                file_p.write(value)

            # square and thumbnail thumb image
            thumb_size = size, size
            try:
                im = Image.open(filename)
            except:
                if os.path.exists(filename):
                    os.remove(filename)
                cls.raise_user_error('not_file_mime_image', {
                        'file_name': file_name,
                        })

            width, height = im.size
            if width > height:
               delta = width - height
               left = int(delta/2)
               upper = 0
               right = height + left
               lower = height
            else:
               delta = height - width
               left = 0
               upper = int(delta/2)
               right = width
               lower = width + upper

            im = im.crop((left, upper, right, lower))
            im.thumbnail(thumb_size, Image.ANTIALIAS)
            im.save(filename)

            cls.write([template], {
                'esale_thumb_filename': digest,
                })


class Product:
    __name__ = 'product.product'
    esale_available = fields.Function(fields.Boolean('eSale'),
        'get_esale_available', searcher='search_esale_available')
    esale_active = fields.Function(fields.Boolean('Active eSale'),
        'get_esale_active', searcher='search_esale_active')
    esale_slug = fields.Char('Slug', translate=True, states=STATES,
        depends=DEPENDS)
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
        # Add code require attribute
        for fname in ('code',):
            fstates = getattr(cls, fname).states
            if fstates.get('required'):
                fstates['required'] = Or(fstates['required'],
                    Bool(Eval('_parent_template', {}).get('esale_available', False)))
            else:
                fstates['required'] = Bool(Eval('_parent_template', {}).get('esale_available', False))
            getattr(cls, fname).depends.append('_parent_template.esale_available')

    @classmethod
    def search(cls, domain, offset=0, limit=None, order=None, count=False,
            query=False):
        for d in domain:
            if d and d[0] == 'esale_slug':
                domain = ['OR', domain[:], ('template.esale_slug', 'ilike', d[2])]
                break
        return super(Product, cls).search(domain, offset=offset, limit=limit,
            order=order, count=count, query=query)

    @fields.depends('template')
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
