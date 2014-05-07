#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from .tools import slugify

__all__ = ['CatalogMenu']


class CatalogMenu(ModelSQL, ModelView):
    "eSale Catalog Menu"
    __name__ = 'esale.catalog.menu'

    name = fields.Char('Name', required=True, translate=True)
    parent = fields.Many2One('esale.catalog.menu', 'Parent', select=True)
    childs = fields.One2Many('esale.catalog.menu', 'parent',
            string='Children')
    active = fields.Boolean('Active')
    default_sort_by = fields.Selection([
            ('', ''),
            ('position', 'Position'),
            ('name', 'Name'),
            ('price', 'Price')
            ], 'Default Product Listing Sort (Sort By)')
    slug = fields.Char('Slug', size=None, translate=True, required=True,
            on_change_with=['name'])
    full_slug = fields.Function(fields.Char('Full Slug'), 'get_full_slug')
    description = fields.Text('Description', translate=True)
    metadescription = fields.Char('MetaDescription', size=155, translate=True)
    metakeyword = fields.Char('MetaKeyword', size=155, translate=True)
    metatitle = fields.Char('MetaTitle', size=155, translate=True)

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_default_sort_by():
        return 'position'

    def on_change_with_slug(self):
        """Create slug from name: az09"""
        name = self.name or ''
        name = slugify(name)
        return name

    @classmethod
    def __setup__(cls):
        super(CatalogMenu, cls).__setup__()
        cls._order.insert(0, ('name', 'ASC'))
        cls._error_messages.update({
            'slug_empty': 'Slug field is empty!',
            'slug_exists': 'Slug %s exists. Get another slug!',
        })

    @classmethod
    def validate(cls, menus):
        super(CatalogMenu, cls).validate(menus)
        cls.check_recursion(menus, rec_name='name')

    def get_full_slug(self, name):
        if self.parent:
            return self.parent.get_full_slug(name) + '/' + self.slug
        else:
            return self.slug

    def get_rec_name(self, name):
        if self.parent:
            return self.parent.get_rec_name(name) + ' / ' + self.name
        else:
            return self.name

    @classmethod
    def search_rec_name(cls, name, clause):
        if isinstance(clause[2], basestring):
            values = clause[2].split('/')
            values.reverse()
            domain = []
            field = 'name'
            for name in values:
                domain.append((field, clause[1], name.strip()))
                field = 'parent.' + field
        else:
            domain = [('name',) + tuple(clause[1:])]
        ids = [w.id for w in cls.search(domain, order=[])]
        return [('parent', 'child_of', ids)]

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
        topmenu = cls.get_topmenu(parent)
        if not topmenu:
            return True
            
        childs = cls.get_allchild(topmenu)
        records = [c.id for c in childs]
        if id:
            records.remove(id)
        menus = cls.search([('slug','=',slug),('id','in',records)])
        if len(menus)>0:
            cls.raise_user_error('slug_exists', slug)
        return True

    @classmethod
    def create(cls, vlist):
        for values in vlist:
            values = values.copy()
            slug = values.get('slug')
            parent = values.get('parent')
            if not slug:
                cls.raise_user_error('slug_empty')
            cls.get_slug(None, slug, parent)
        return super(CatalogMenu, cls).create(vlist)

    @classmethod
    def write(cls, records, values):
        values = values.copy()
        for record in records:
            slug = values.get('slug')
            parent = values.get('parent')
            if slug:
                if not parent:
                    parent = cls(record).parent.id
                cls.get_slug(record.id, slug, parent)
        return super(CatalogMenu, cls).write(records, values)
