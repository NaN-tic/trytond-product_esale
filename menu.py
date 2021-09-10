# This file is part product_esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, DeactivableMixin, fields, tree
from trytond.pool import Pool
from .tools import slugify
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['CatalogMenu']


class CatalogMenu(tree(separator=' / '), DeactivableMixin, ModelSQL, ModelView):
    "eSale Catalog Menu"
    __name__ = 'esale.catalog.menu'

    name = fields.Char('Name', required=True, translate=True)
    parent = fields.Many2One('esale.catalog.menu', 'Parent', select=True)
    childs = fields.One2Many('esale.catalog.menu', 'parent',
            string='Children')
    default_sort_by = fields.Selection([
            ('', ''),
            ('position', 'Position'),
            ('name', 'Name'),
            ('price', 'Price'),
            ('date', 'Date'),
            ], 'Default Product Listing Sort (Sort By)')
    slug = fields.Char('Slug', size=None, translate=True, required=True)
    full_slug = fields.Function(fields.Char('Full Slug'), 'get_full_slug')
    description = fields.Text('Description', translate=True)
    metadescription = fields.Char('MetaDescription', size=155, translate=True)
    metakeyword = fields.Char('MetaKeyword', size=155, translate=True)
    metatitle = fields.Char('MetaTitle', size=155, translate=True)
    include_in_menu = fields.Boolean('Included in Menu')

    @staticmethod
    def default_default_sort_by():
        return 'position'

    @staticmethod
    def default_include_in_menu():
        return True

    @fields.depends('name', 'slug')
    def on_change_name(self):
        if self.name and not self.slug:
            self.slug = slugify(self.name)

    @classmethod
    def __setup__(cls):
        super(CatalogMenu, cls).__setup__()
        cls._order.insert(0, ('name', 'ASC'))

    @classmethod
    def copy(cls, menus, default=None):
        raise UserError(gettext('product_esale.not_copy'))

    def get_full_slug(self, name):
        if self.parent:
            return self.parent.get_full_slug(name) + '/' + self.slug
        else:
            return self.slug

    @classmethod
    def get_topmenu(cls, parent):
        """Get Top Menu
        :param id: int
        :return id
        """
        top_id = False
        parent_id = False

        if not parent:
            return top_id

        cat_parent = parent
        if parent:
            parent_id = cat_parent

        while(parent_id):
            top_id = parent_id
            cat_parent = cls(top_id).parent
            parent_id = cat_parent

        return top_id

    @classmethod
    def get_allchild(cls, menu):
        """Get All Childs Menu
        :param menu: int
        :return list objects
        """
        childs = []
        for child in cls(menu).childs:
            childs.append(child)
            childs.extend(cls.get_allchild(child.id))
        return childs

    @classmethod
    def get_slug(cls, id, slug, parent):
        """Get another menu is same slug
        Slug is identificator unique
        :param id: int
        :param slug: str
        :return True or False
        """
        Config = Pool().get('product.configuration')
        config = Config(1)
        if not config.check_slug:
            return True

        topmenu = cls.get_topmenu(parent)
        if not topmenu:
            return True

        childs = cls.get_allchild(topmenu)
        records = [c.id for c in childs]
        if id and id in records:
            records.remove(id)
        menus = cls.search([('slug','=',slug),('id','in',records)])
        if len(menus)>0:
            raise UserError(gettext('product_esale.slug_exists', slug=slug))
        return True

    @classmethod
    def create(cls, vlist):
        for values in vlist:
            values = values.copy()
            slug = values.get('slug')
            parent = values.get('parent')
            if not slug:
                raise UserError(gettext('product_esale.slug_empty'))
            cls.get_slug(None, slug, parent)
        return super(CatalogMenu, cls).create(vlist)

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        for records, values in zip(actions, actions):
            slug = values.get('slug')
            parent = values.get('parent')
            if slug:
                for record in records:
                    if parent:
                        parent = cls(record).parent.id
                    cls.get_slug(record.id, slug, parent)
        return super(CatalogMenu, cls).write(*args)
