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
import logging
import textwrap
import traceback

from requests import Request, Session
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from requests.exceptions import RequestException

from odoo import api, models, fields, registry, tools, SUPERUSER_ID, _
from odoo.tools import ignore, mute_logger
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.addons.muk_webhooks.tools import auth, oauth, encoder, utils

_logger = logging.getLogger(__name__)


class ServerActions(models.Model):
    
    _inherit = 'ir.actions.server'

    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    state = fields.Selection(
        selection_add=[
            ('request', 'Request')
        ],
        ondelete={
            'request': 'cascade'
        }
    )
    
    request_address = fields.Char(
        string="Address",
        states={
            'request': [('required', True)]
        }
    )
    
    request_method = fields.Selection(
        selection=[
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE")
        ],
        string="Method",
        states={
            'request': [('required', True)]
        },
        default='POST'
    )
    
    request_timeout = fields.Integer(
        string="Timeout",
        states={
            'webhook': [('required', True)]
        },
        default=25
    )
    
    request_secure = fields.Boolean(
        compute='_compute_request_secure',
        string="Secure"
    )
     
    request_verify_ssl = fields.Boolean(
        string="Verify SSL",
        default=True
    )

    request_authentication = fields.Boolean(
        string="Apply Authentication",
        default=False
    )

    request_authentication_id = fields.Many2one(
        comodel_name='muk_webhooks.authentication',
        string="Authentication",
        ondelete = "restrict",
    )

    request_authentication_type = fields.Selection(
        related='request_authentication_id.authentication_type'
    )
    
    request_authentication_user = fields.Char(
        related='request_authentication_id.user'
    )
     
    request_authentication_password = fields.Char(
        related='request_authentication_id.password'
    )
     
    request_authentication_token = fields.Char(
        related='request_authentication_id.token'
    )
     
    request_authentication_grant = fields.Selection(
        related='request_authentication_id.grant'
    )
     
    request_authentication_client_key = fields.Char(
        related='request_authentication_id.client_key'
    )
     
    request_authentication_client_secret = fields.Char(
        related='request_authentication_id.client_secret'
    )

    request_authentication_include_client_key = fields.Boolean(
        related='request_authentication_id.include_client_key'
    )

    request_authentication_token_url = fields.Char(
        related='request_authentication_id.token_url'
    )

    request_authentication_parameter_ids = fields.One2many(
        related='request_authentication_id.parameter_ids'
    )

    request_adapt_headers = fields.Boolean(
        string="Adapt Headers",
        default=False
    )    
    
    request_headers_value_ids = fields.One2many(
        comodel_name='muk_webhooks.header',
        inverse_name='action_id',
        string="Header Values"
    )
    
    request_headers_code = fields.Text(
        string="Header Code",
        default=textwrap.dedent("""\
            # Adapt the headers of the request to your requirements. 
            #
            # Available variables:
            #
            #  - user: User who triggered the action
            #  - headers: Current headers of the request
            #  - env: Odoo Environment on which the action is triggered
            #  - model: Odoo Model of the record on which the action is triggered; is a void recordset
            #  - record: Record on which the action is triggered; may be void
            #  - records: Recordset of all records on which the action is triggered in multi-mode; may be void
            #  - time, datetime, dateutil, timezone, json: Useful Python libraries
            #  - b64encode, b64decode: Base64 converter to encode and decode binary data
            #  - log: log(message, level='info'): Logging function to record debug information in ir.logging table
            #  - UserError: Warning Exception to use with raise
            #
            # To override the headers, assign: headers = {'key': 'value'}\n
        """)
    )
    
    request_adapt_payload = fields.Boolean(
        string="Adapt Payload",
        default=False
    )    
    
    request_field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        relation='rel_server_action_request_fields',
        domain="[('model_id', '=', model_id)]", 
        string="Request Fields"
    )
    
    request_payload_code = fields.Text(
        string="Payload",
        default=textwrap.dedent("""\
            # Adapt the payload of the request to your requirements. 
            #
            # Available variables:
            #
            #  - user: User who triggered the action
            #  - env: Odoo Environment on which the action is triggered
            #  - model: Odoo Model of the record on which the action is triggered; is a void recordset
            #  - record: Record on which the action is triggered; may be void
            #  - records: Recordset of all records on which the action is triggered in multi-mode; may be void
            #  - time, datetime, dateutil, timezone, json: Useful Python libraries
            #  - b64encode, b64decode: Base64 converter to encode and decode binary data
            #  - log: log(message, level='info'): Logging function to record debug information in ir.logging table
            #  - UserError: Warning Exception to use with raise
            #
            # To extend the payload, assign: content = {...}
            # To override the payload, assign: payload = {...}\n
        """)
    )
    
    request_process_response = fields.Boolean(
        string="Process Response",
        default=False
    ) 

    request_process_response_code = fields.Text(
        string="Response",
        default=textwrap.dedent("""\
            # Process the response of the request. 
            #
            # Available variables:
            #
            #  - user: User who triggered the action
            #  - request: Request send by the action
            #  - response: Response received when the request was sent
            #  - env: Odoo Environment on which the action is triggered
            #  - model: Odoo Model of the record on which the action is triggered; is a void recordset
            #  - record: Record on which the action is triggered; may be void
            #  - records: Recordset of all records on which the action is triggered in multi-mode; may be void
            #  - time, datetime, dateutil, timezone, json: Useful Python libraries
            #  - b64encode, b64decode: Base64 converter to encode and decode binary data
            #  - log: log(message, level='info'): Logging function to record debug information in ir.logging table
            #  - UserError: Warning Exception to use with raise
            #
            # To return an action, assign: action = {...}\n
        """)
    )
     
    request_handle_error_code = fields.Text(
        string="Handle Error",
        default=textwrap.dedent("""\
            # Handle a timeout or an error returned by sending the request. 
            #
            # Available variables:
            #
            #  - user: User who triggered the action
            #  - request: Request send by the action
            #  - exception: Exception which was raised during the process; may be void
            #  - response: Response received when the request was sent; may be void
            #  - env: Odoo Environment on which the action is triggered
            #  - model: Odoo Model of the record on which the action is triggered; is a void recordset
            #  - record: Record on which the action is triggered; may be void
            #  - records: Recordset of all records on which the action is triggered in multi-mode; may be void
            #  - time, datetime, dateutil, timezone, json: Useful Python libraries
            #  - b64encode, b64decode: Base64 converter to encode and decode binary data
            #  - log: log(message, level='info'): Logging function to record debug information in ir.logging table
            #  - UserError: Warning Exception to use with raise
            #
            # To return the exception to the system write: raise exception
            # To return an action, assign: action = {...}\n
        """)
    )
    
    request_logging = fields.Boolean(
        string="Logging",
        default=True,
    )
    
    request_show_logging = fields.Boolean(
        compute='_compute_request_show_logging',
        string="Show Logging",
    )
    
    request_logging_ids = fields.One2many(
        comodel_name='muk_webhooks.logging',
        inverse_name='action_id',
        string="Request Logs"
    )
    
    #----------------------------------------------------------
    # Constrains
    #----------------------------------------------------------
     
    @api.constrains('request_headers_code')
    def _check_request_headers_code(self):
        for record in self.sudo().filtered('request_headers_code'):
            message = test_python_expr(expr=record.request_headers_code.strip(), mode="exec")
            if message:
                raise ValidationError(message)
     
    @api.constrains('request_payload_code')
    def _check_request_payload_code(self):
        for record in self.sudo().filtered('request_payload_code'):
            message = test_python_expr(expr=record.request_payload_code.strip(), mode="exec")
            if message:
                raise ValidationError(message)
     
    @api.constrains('request_process_response_code')
    def _check_request_process_response_code(self):
        for record in self.sudo().filtered('request_process_response_code'):
            message = test_python_expr(expr=record.request_process_response_code.strip(), mode="exec")
            if message:
                raise ValidationError(message)
     
    @api.constrains('request_handle_error_code')
    def _check_request_handle_error_code(self):
        for record in self.sudo().filtered('request_handle_error_code'):
            message = test_python_expr(expr=record.request_handle_error_code.strip(), mode="exec")
            if message:
                raise ValidationError(message)
    
    #----------------------------------------------------------
    # Read
    #----------------------------------------------------------
     
    @api.depends('request_address')
    def _compute_request_secure(self):
        for record in self:
            record.request_secure = record.request_address and \
                    record.request_address.startswith('https')
    
    def _compute_request_show_logging(self):
        self.update({'request_show_logging': tools.config.get('webhook_logging', True)})
    
    #----------------------------------------------------------
    # Helpers
    #----------------------------------------------------------
   
    @api.model
    def _get_eval_context(self, action):
        eval_context = super(ServerActions, self)._get_eval_context(action)
        if action.state == 'request':
            eval_context['json'] = tools.safe_eval.json
        return eval_context

    @api.model
    def _request_prepare_session(self, action):
        if action.request_authentication_id:
            return action.request_authentication_id._prepare_session()
        return Session()
    
    @api.model
    def _request_build_headers(self, action, eval_context):
        request_headers = {}
        if action.request_headers_value_ids:
            for pair in action.request_headers_value_ids.read(['name', 'value']):
                request_headers[pair['name']] = pair['value']
        if action.request_adapt_headers and action.request_headers_code:
            header_eval_context = eval_context.copy()
            header_eval_context['headers'] = request_headers
            safe_eval(
                action.request_headers_code.strip(), 
                header_eval_context,
                mode="exec", 
                nocopy=True
            )
            request_headers.update(header_eval_context.get('headers', {}))
        return request_headers
    
    @api.model
    def _request_build_payload(self, action, eval_context):
        request_content, request_payload = None, None
        fields = action.request_field_ids.mapped('name')

        if action.request_adapt_payload and action.request_payload_code:
            payload_eval_context = eval_context.copy()
            safe_eval(
                action.request_payload_code.strip(), 
                payload_eval_context, 
                mode="exec", 
                nocopy=True
            )
            if 'content' in payload_eval_context:
                request_content = payload_eval_context['content']
            elif 'payload' in payload_eval_context:
                request_payload = payload_eval_context['payload']
        
        if request_payload is not None:
            return request_payload

        if fields or request_content:
            user = eval_context.get('user')
            records = eval_context.get('records')
            request_payload = {
                'name': action.name,
                'uid': eval_context.get('uid'),
                'user': user and user.name,
                'model': action.model_name,
            }
            if request_content:
                request_payload['content'] = request_content
            if fields and records:
                request_payload['records'] = json.dumps(
                    records.read(fields=fields or None),
                    cls=encoder.RequestEncoder
                )
        return request_payload
    
    @api.model
    def _request_handle_response(self, action, request, response, eval_context):
        if action.request_process_response and action.request_process_response_code:
            response_eval_context = eval_context.copy()
            response_eval_context.update({
                'request': request, 
                'response': response
            })
            safe_eval(
                action.request_process_response_code.strip(), 
                response_eval_context, 
                mode="exec",
                nocopy=True
            )
            if 'action' in response_eval_context:
                return response_eval_context['action']
        return None
    
    @api.model
    def _request_handle_error(self, action, request, response, exception, eval_context):
        if action.request_process_response and action.request_handle_error_code:
            error_eval_context = eval_context.copy()
            error_eval_context.update({
                'request': request, 
                'response': response,
                'exception': exception,
            })
            safe_eval(
                action.request_handle_error_code.strip(), 
                error_eval_context, 
                mode="exec",
                nocopy=True
            )
            if 'action' in error_eval_context:
                return error_eval_context['action']
        return None
    
    @api.model
    def _reuqest_parse_values(self, eval_context, request=None, response=None, result=None, exception=None):
        vals = {'request': None,  'response': None, 'exception': None, 'result': None}
        if request is not None:
            vals['request'] = encoder.encode_http_data(
                request.method, request.url, request.headers, request.body
            )
        if response is not None:
            vals['response'] = encoder.encode_http_data(
                response.status_code, response.url, response.headers, response.text
            )
        if result is not None:
            vals['result'] = tools.ustr(result)
        if exception is not None:
            vals['exception'] = '{}\n\n{}'.format(
                getattr(exception, 'message', tools.ustr(exception)), 
                ''.join(traceback.format_tb(exception.__traceback__))
            )
        vals['context_data'] = json.dumps({
            'active_model': getattr(eval_context.get('model'), '_name', False),
            'active_id': getattr(eval_context.get('record'), 'id', False),
            'active_ids': getattr(eval_context.get('records'), 'ids', False),
        }, indent=4, sort_keys=True)
        return vals

    @api.model
    def _reuqest_log_message(self, action, request, response, result, exception, eval_context):
        vals = self._reuqest_parse_values(eval_context, request, response, result, exception)
        with ignore(Exception), mute_logger('odoo.sql_db'), registry(self.env.cr.dbname).cursor() as cr:
            api.Environment(cr, SUPERUSER_ID, {})['muk_webhooks.logging'].create({**vals, **{
                'log_type': vals.get('exception') and 'error' or 'request',
                'action_id': action.id,
                'user_id': self.env.uid,
            }})
    
    @api.model
    def _request_action_send(self, action, eval_context):
        request_session, action_request, action_response = None, None, None
        action_result, action_error = None, None
        try:
            with self.env.cr.savepoint():
                request_session = self._request_prepare_session(action)
                headers = self._request_build_headers(action, eval_context)
                payload = self._request_build_payload(action, eval_context)

                verify = action.request_verify_ssl
                if verify and tools.config.get('webhook_verify', False):
                    verify = tools.config.get('webhook_verify', True)

                request_data = {'data': payload}
                if utils.check_json_content_type(headers):
                    request_data = {'json': payload}

                action_response = request_session.request(
                    action.request_method,
                    action.request_address,
                    headers=headers,
                    timeout=action.request_timeout,
                    verify=verify,
                    **request_data
                )
                action_request = action_response.request
                action_response.raise_for_status()
                action_result = self._request_handle_response(
                    action, action_request, action_response, eval_context
                )
        except Exception as exc:
            _logger.exception('Request: {}'.format(
                action.request_address
            ))
            action_error = exc
            action_result = self._request_handle_error(
                action, action_request, action_response, exc, eval_context
            )
        finally:
            if request_session is not None:
                request_session.close()
        return (
            action_request, action_response, action_result, action_error,
        )
    
    def _run_action_request_multi(self, eval_context=None):
        request, response, result, exception = self._request_action_send(
            self, eval_context or {}
        )
        if tools.config.get('webhook_logging', True) and self.request_logging:
            self._reuqest_log_message(
                self, request, response, result, exception, eval_context or {}
            )
        return result
        
    #----------------------------------------------------------
    # Actions
    #----------------------------------------------------------
    
    def action_open_report(self):
        return {
            'name': _("Analytics"),
            'type': 'ir.actions.act_window',
            'res_model': 'muk_webhooks.logging',
            'views': [(False, 'graph'), (False, 'pivot'), (False, 'tree'), (False, 'form')],
            'domain': [('action_id', 'in', self.ids)],
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_open_preview(self):
        self.ensure_one()
        return {
            'name': _("Preview Request for %s") % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'muk_webhooks.preview',
            'views': [(False, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_action_id': self.id
            }
        }
        