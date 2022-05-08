###################################################################################
#
#    Copyright (c) 2017-today MuK IT GmbH.
#
#    This file is part of MuK Webhooks for Odoo
#    (see https://mukit.at).
#
#    MuK Proprietary License v1.0
#
#    This software and associated files (the "Software") may only be used
#    (executed, modified, executed after modifications) if you have
#    purchased a valid license from MuK IT GmbH.
#
#    The above permissions are granted for a single database per purchased
#    license. Furthermore, with a valid license it is permitted to use the
#    software on other databases as long as the usage is limited to a testing
#    or development environment.
#
#    You may develop modules based on the Software or that use the Software
#    as a library (typically by depending on it, importing it and using its
#    resources), but without copying any source code or material from the
#    Software. You may distribute those modules under the license of your
#    choice, provided that this license is compatible with the terms of the
#    MuK Proprietary License (For example: LGPL, MIT, or proprietary licenses
#    similar to this one).
#
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###################################################################################


import json

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression

from odoo.addons.muk_webhooks.tools import encoder


class WebhookPreview(models.TransientModel):
    
    _name = 'muk_webhooks.preview'
    _description = 'Request Preview'

    #----------------------------------------------------------
    # Selection
    #----------------------------------------------------------
    
    @api.model
    def _selection_resource_reference(self):
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]

    #----------------------------------------------------------
    # Default
    #----------------------------------------------------------
    
    @api.model
    def default_get(self, fields):
        result = super(WebhookPreview, self).default_get(fields)
        if result.get('action_id', False):
            domain = self.env.context.get('preview_domain', [])
            action = self.env['ir.actions.server'].browse(result['action_id'])
            record = self.env[action.model_id.model].search(domain, limit=1)
            if record:
                result['resource_reference'] = '{},{}'.format(
                    action.model_id.model, record.id
                )
            else:
                result['has_no_record'] = True
        return result
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------

    action_id = fields.Many2one(
        comodel_name='ir.actions.server',
        string="Server Action",
        ondelete='cascade', 
        required=True,
        readonly=True,
    )
    
    state = fields.Selection(
        selection=[
            ('setup', 'Setup'),
            ('request', 'Request'),
        ],
        string="State",
        default='setup',
    )
    
    model_id = fields.Many2one(
        comodel_name='ir.model', 
        string="Hook Model", 
        related='action_id.model_id',
        readonly=True,
    )
    
    resource_reference = fields.Reference(
        selection='_selection_resource_reference',
        string="Preview Record",
        states={
            'request': [('readonly', True)], 
        },
    )
    
    has_no_record = fields.Boolean(
        compute='_compute_has_no_record',
        string="No Record", 
        store=True,
        states={
            'request': [('readonly', True)], 
        },
    )
    
    send_request = fields.Boolean(
        string="Send Request", 
        default=True,
        states={
            'request': [('readonly', True)], 
        },
        help="If set to False no request is send."
    )
    
    reset_changes = fields.Boolean(
        string="Reset Changes", 
        default=True,
        states={
            'request': [('readonly', True)], 
        },
        help="If set to True changes won't be saved."
    )

    context_data = fields.Text(
        string="Context Data",
        readonly=True,
    )
    
    request = fields.Text(
        string="Request",
        readonly=True,
    )
    
    response = fields.Text(
        string="Response",
        readonly=True,
    )
    
    result = fields.Text(
        string="Result",
        readonly=True,
    )
    
    exception = fields.Text(
        string="Exception",
        readonly=True,
    )
    
    #----------------------------------------------------------
    # Read
    #----------------------------------------------------------
    
    @api.depends('model_id')
    def _compute_has_no_record(self):
        for record in self:
            if not record.model_id:
                record.has_no_record = True
            else:
                record.has_no_record = (
                    self.env[record.model_id.model].search_count([]) == 0
                )
    
    #----------------------------------------------------------
    # Actions
    #----------------------------------------------------------
    
    def action_send_request(self):
        action = self.action_id.with_context(
            active_id=self.resource_reference and self.resource_reference.id or False,
            active_ids=self.resource_reference and [self.resource_reference.id] or [],
            active_model=self.model_id.model,
        )
        eval_context = action._get_eval_context(action) or {}
        
        self.env.cr.execute('SAVEPOINT webhook_preview')
        if self.send_request:
            request, response, result, exception = action._request_action_send(
                action, eval_context
            )
        else:
            headers = action._request_build_headers(action, eval_context)
            payload = action._request_build_payload(action, eval_context)
        if self.reset_changes:
                self._cr.execute('ROLLBACK TO SAVEPOINT webhook_preview')
                self.pool.clear_caches()
                self.pool.reset_changes()
        else:
            self._cr.execute('RELEASE SAVEPOINT webhook_preview')

        wizard_vals = {'state': 'request'}
        if self.send_request:
            wizard_vals.update(action._reuqest_parse_values(
                eval_context, request, response, result, exception
            ))
        else:
            wizard_vals['request'] = encoder.encode_http_data(
                '<>', action.request_address, headers, json.dumps(payload)
            )
        self.write(wizard_vals)
        
        return {
            'name': _("Preview Request for %s") % action.name,
            'type': 'ir.actions.act_window',
            'res_model': 'muk_webhooks.preview',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }