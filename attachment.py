#This file is part product_esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Attachment']
__metaclass__ = PoolMeta


class Attachment:
    __name__ = 'ir.attachment'
    esale_available  = fields.Boolean('Available eSale',
        help='This image are available in your e-commerce.')
    esale_base_image = fields.Boolean('Base Image')
    esale_small_image = fields.Boolean('Small Image')
    esale_thumbnail = fields.Boolean('Thumbnail Image')
    esale_exclude = fields.Boolean('Exclude',
        help='Defines whether the image will associate only to one of '
            'three image types ')
    esale_position = fields.Integer('Position',
        help='Image file position ')

    @classmethod
    def __setup__(cls):
        super(Attachment, cls).__setup__()
        cls._error_messages.update({
            'delete_esale_attachment': 'Attachment %s is esale active. '
                'Descheck exclude field to dissable esale attachments',
        })

    @staticmethod
    def default_esale_base_image():
        return True

    @staticmethod
    def default_esale_small_image():
        return True

    @staticmethod
    def default_esale_thumbnail():
        return True

    @staticmethod
    def default_esale_position():
        return 1

    @classmethod
    def delete(cls, attachments):
        for attachment in attachments:
            if attachment.esale_available:
                cls.raise_user_error('delete_esale_attachment', (attachment.rec_name,))
        super(Attachment, cls).delete(attachments)
