import base64
from odoo import models, fields, api
from odoo.tools import ImageProcess


class aircraft_type(models.Model):
    _name = 'avia.aircraft_types'

    name = fields.Char(string="Aircraft type name", required=True)
    code = fields.Char(string="Aircraft type code", required=True)
    description = fields.Char(string="Aircraft type description")

class aircraft_status(models.Model):
    _name = 'avia.aircraft_status'

    name = fields.Char(string="Aircraft status name", required=True)
    code = fields.Char(string="Aircraft status code", required=True)
    description = fields.Char(string="Aircraft status description")


class aircrafts(models.Model):
    _name = 'avia.aircrafts'

    board_number = fields.Char(string=" Board Number", required=True)
    serial_number = fields.Char(string="Serial board number", required=True)
    description = fields.Char(string="Aircraft description")
    type_id = fields.Many2one('avia.aircraft_types', string='Aircraft type' , index=True)
    status_id = fields.Many2one('avia.aircraft_status', string='Aircraft status', index=True)
    foto = fields.Image(string='Aircraft photo', max_width=1024, max_height=1024)
    avatar = fields.Image(string='Aircraft avatar', max_width=256, max_height=256, compute="_compute_images")

    @api.depends('foto')
    def _compute_images(self):
#        resized_images = image_resize_image_small(self.foto, return_big=True,avoid_resize_medium=True)
#         self.image = tools.image_resize_image_medium(self.image, size=(256, 256)).
#        self.avatar = resized_images['image_small']
#        self.avatar = tools.image_resize_image(self.foto,(64, 64), 'base64', None, False)

        for row in self:
            image = ImageProcess(base64.b64decode(row.foto))
            # resize uploaded image into 250 X 250
            w, h = image.image.size
            square_size = w if w > h else h
            image.crop_resize(square_size, square_size)
            image.image = image.image.resize((128, 128))
#            image.operationsCount += 1
            row.avatar = base64.b64encode(image.image_quality(output_format='PNG'))
