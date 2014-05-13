#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
import logging

try:
    import slug
except ImportError:
    logging.getLogger('product esale').error(
            'Unable to import slug. Install slug package.')

def slugify(value):
    """Convert value to slug: az09 and replace spaces by -"""
    try:
        if isinstance(value, unicode):
            name = slug.slug(value)
        else:
            name = slug.slug(unicode(value, 'UTF-8'))
    except:
        name = ''
    return name

def seo_lenght(string):
    '''Get first 155 characters from string'''
    if len(string) > 155:
        return '%s...' % (string[:152])
    return string
