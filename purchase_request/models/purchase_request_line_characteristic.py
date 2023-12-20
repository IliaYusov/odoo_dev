from odoo import api, fields, models, _


class PurchaseRequestLineCharacteristic(models.Model):
    """
        Риторический вопрос, как заставить себя делать нижеидущую хрень?!
    """
    _name = 'purchase.request.line.characteristic'
    _description = "Purchase Request Line Characteristic"
    _order = 'request_line_id, sequence, id'

    request_line_id = fields.Many2one('purchase.request.line', string='Request Line', ondelete='cascade',
                                      copy=True, index=True)
    request_line_estimation_id = fields.Many2one('purchase.request.line.estimation', string='Request Line Estimation',
                                                 ondelete='cascade', copy=True, index=True)
    sequence = fields.Integer(string='Sequence', copy=True, default=1)
    characteristic_id = fields.Many2one('purchase.request.component.characteristic', string='Characteristic',
                                        ondelete='restrict', copy=True)
    characteristic_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', ondelete='restrict', copy=True)
    characteristic_value = fields.Text(string='Value', copy=True)
