from odoo import _, models, fields, api
from odoo.exceptions import ValidationError

class molot_cutting_tool(models.Model):
    _name = 'molot.cutting_tool'
    _description = "cutting tool"
    name = fields.Char(string="Name", required=True)
    artikul = fields.Char(string="Artikul", required=True, index=True)
    unit_of_msrmnt_id = fields.Many2one('molot.unit_of_measurement', string='unit of measurement', required=True)
    descr = fields.Text(string="Description")
    tool_group_id= fields.Many2one('molot.tool_group', string='tool group', required=True)
    tool_class_id = fields.Many2one('molot.tool_class', string='tool class', required=True)
    tools_manufacturers_ids = fields.One2many(
        comodel_name='molot.tools_manufacturers',
        inverse_name='tool_id',
        string="cutting tools manufacturers",
        copy=False, auto_join=True)
    cutting_tool_parameters_ids = fields.One2many(
        comodel_name='molot.cutting_tool_parameters',
        inverse_name='tool_id',
        string="cutting tool parameters",
        copy=False, auto_join=True)

    cutting_tool_assembling_spec_ids = fields.One2many(
        comodel_name = 'molot.cutting_tool_assembling_spec',
        inverse_name = 'maintool_id',
        string = "Assembling specifications",
        copy = True, auto_join = True)


    mandrel_id = fields.Many2one('molot.mandrel', string='tool mandrel')
    alloy_id = fields.Many2one('molot.alloy', string='tool alloy')
    number_of_cutting_edges = fields.Integer(string="number_of_cutting_edges")
    number_of_steps = fields.Integer(string="number_of_steps")
    weight_kg = fields.Float(string="weight_kg")
    type_of_use = fields.Many2one('molot.type_of_use', string='tool Type_of_use')
    cad_number = fields.Char(string="CAD number")
    macro_name = fields.Char(string="Macro name")
    _sql_constraints = [
        ('unique_artikul', 'unique(artikul)', 'artikul must be unique'),
    ]
    @api.model_create_multi
    # копируем все свойства к создаваемому инструменту из cutting_tool_parameters_base
    def create(self, val_list):
        cutting_tools = super(molot_cutting_tool, self).create(val_list)
        for cutting_tool in cutting_tools:
            parameters_base = self.env['molot.cutting_tool_parameters_base'].search([])
            if cutting_tools.id:
                for parameter_base in parameters_base:
                    tool_parameters_create_vals = []
                    tool_parameters_create_vals.append(dict(
                                tool_id = cutting_tool.id,
                                parameter_id = parameter_base.id,
                                parameter_name = parameter_base.name,
                                parameter_code = parameter_base.code
                    ))
                    self.env['molot.cutting_tool_parameters'].create(tool_parameters_create_vals)
        self.env.flush_all()
        return cutting_tools

class molot_mandrel(models.Model):
    _name = 'molot.mandrel'
    _description = "mandrel"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)

class molot_alloy(models.Model):
    _name = 'molot.alloy'
    _description = "alloy"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)

class molot_type_of_use(models.Model):
    _name = 'molot.type_of_use'
    _description = "type of use"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)

class molot_unit_of_measurement(models.Model):
    _name = 'molot.unit_of_measurement'
    _description = "unit of measurement"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)

class molot_cutting_tool_parameters_base(models.Model):
    _name = 'molot.cutting_tool_parameters_base'
    _description = "cutting tool parameters base"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    unit_of_msrmnt_id=fields.Many2one('molot.unit_of_measurement', string='unit of measurement', required=True)
    descr = fields.Text(string="Description")

    def copy_check_exist_parameters_to_all_tools(self):
        base_parameters = self.env['molot.cutting_tool_parameters_base'].search([])
        cutting_tools = self.env['molot.cutting_tool'].search([])
        for base_parameter in base_parameters:
            for cutting_tool in cutting_tools:
                exist_tool_parameters = self.env['molot.cutting_tool_parameters'].search([('tool_id.id','=',cutting_tool.id),('parameter_id.id','=',base_parameter.id)])
                if not exist_tool_parameters:
                    tool_parameters_create_vals = []
                    tool_parameters_create_vals.append(dict(
                        tool_id=cutting_tool.id,
                        parameter_id=base_parameter.id
                    ))
                    self.env['molot.cutting_tool_parameters'].create(tool_parameters_create_vals)

class molot_cutting_tool_parameters(models.Model):
    _name = 'molot.cutting_tool_parameters'
    _description = "cutting tool parameters"
    tool_id = fields.Many2one('molot.cutting_tool', string='cutting tool', required=True,  ondelete='cascade',index=True, )
    parameter_id = fields.Many2one('molot.cutting_tool_parameters_base', string='tool parameter', required=True)
    parameter_name = fields.Char(string='tool parameter name', compute='_computeCode_name')
    parameter_code = fields.Char(string='tool parameter code', compute='_computeCode_name')
    param_value = fields.Float(string='Value parameter')

    @api.depends('parameter_id','parameter_id.name','parameter_id.code')
    def _computeCode_name(self):
        for row in self:
            row.parameter_name = row.parameter_id.name
            row.parameter_code = row.parameter_id.code
        return False

class molot_cutting_tool_assembling_spec(models.Model):
    _name = 'molot.cutting_tool_assembling_spec'
    _description = "cutting tool assembling spec"

    def _get_cutting_tools_list(self):
        print('befor for rec in self ')
        for rec in self:
            print('rec.maintool_id.id = ', rec.maintool_id.id)
            domain = [('id', '!=', rec.maintool_id.id)]
            return domain

    maintool_id = fields.Many2one('molot.cutting_tool', string='cutting tool (assembling)', required=True,  ondelete='cascade',index=True, )
    specification_tool_id = fields.Many2one('molot.cutting_tool', string='cutting tool specification', required=True, index=True, domain=_get_cutting_tools_list,)
    spec_number = fields.Integer(string=' specification number', required=True)
    artikul = fields.Char(string='tool artikul', compute='_compute_artikul_name')
    quantity = fields.Integer(string='Quantity')

    @api.constrains('specification_tool_id')
    def _check_date_end(self):
        for record in self:
            if record.specification_tool_id.id == record.maintool_id.id:
                raisetext = _("assembling could not be from itself")
                raise ValidationError(raisetext)
    @api.depends('specification_tool_id','specification_tool_id.name','specification_tool_id.artikul')
    def _compute_artikul_name(self):
        for row in self:
            row.artikul = row.specification_tool_id.artikul
        return False

class molot_tools_manufacturers(models.Model):
    _name = 'molot.tools_manufacturers'
    _description = "cutting tools manufacturers"
    # name = fields.Char(string="Name", required=True)
    # code = fields.Char(string="Code", required=True)
    # descr = fields.Text(string="Description")
    tool_id = fields.Many2one('molot.cutting_tool', string='cutting tool', required=True,  ondelete='cascade',index=True, )
    manufacturer_id = fields.Many2one('molot.manufacturer', string='tool manufacturer', required=True)
    manufacturers_artikul = fields.Char(string="manufacturers artikul")
    descr = fields.Text(string="Description")

class molot_tool_group(models.Model):
    _name = 'molot.tool_group'
    _description = "tool group"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    descr = fields.Text(string="Description")

class molot_tool_class(models.Model):
        _name = 'molot.tool_class'
        _description = "molot tool class"
        name = fields.Char(string="Name", required=True)
        code = fields.Char(string="Code", required=True)
        descr = fields.Text(string="Description")


class molot_manufacturer(models.Model):
    _name = 'molot.manufacturer'
    _description = "molot manufacturer"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    descr = fields.Text(string="Description")

class molot_mol(models.Model):
    _name = 'molot.mol'
    _description = "molot mol"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    descr = fields.Text(string="Description")

class molot_workplace(models.Model):
    _name = 'molot.workplace'
    _description = "molot mol"
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    descr = fields.Text(string="Description")

