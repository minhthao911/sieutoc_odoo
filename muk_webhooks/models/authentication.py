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

from odoo import api, models, fields, tools, _
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.addons.muk_webhooks.tools import auth, oauth, encoder

_logger = logging.getLogger(__name__)


class WebhookAuthentication(models.Model):
    
    _name = 'muk_webhooks.authentication'
    _description = 'Webhook Authentication'

    #----------------------------------------------------------
    # Selections
    #----------------------------------------------------------

    def _authentication_selection(self):
        selection = [
            ('base', 'Basic'),
            ('digest', 'Digest'),
            ('token', 'Token'),
        ]
        if oauth.active_authentication:
            selection.extend([
                ('oauth2', 'OAuth2')
            ])
        return selection

    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------

    name = fields.Char(
        string="Name",
        required=True,
    )

    authentication_type = fields.Selection(
        selection='_authentication_selection',
        string="Authentication Type",
        required=True,
    )
    
    user = fields.Char(
        string="User"
    )

    password = fields.Char(
        string="Password"
    )

    token = fields.Char(
        string="Access Token"
    )

    grant = fields.Selection(
        selection=[
            ('password', 'Password Credentials'),
            ('client_credentials', ' Client Credentials')
        ],
        string="Grant Type",
        default='password'
    )

    client_key = fields.Char(
        string="Client ID"
    )

    client_secret = fields.Char(
        string="Client Secret"
    )

    include_client_key = fields.Boolean(
        string="Include Client ID",
        help="Should the request body include the Client ID parameter.",
        default=True,
    )

    token_url = fields.Char(
        string="Token URL"
    )

    parameter_ids = fields.One2many(
        comodel_name='muk_webhooks.authentication.parameter',
        inverse_name='authentication_id',
        string="Parameters"
    )

    webhook_ids = fields.One2many(
        comodel_name='ir.actions.server',
        inverse_name='request_authentication_id',
        string="Webhooks"
    )

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    def _prepare_session(self):
        if self.authentication_type in ['base', 'digest', 'token']:
            session = Session()
            if self.authentication_type == 'base':
                session.auth = HTTPBasicAuth(self.user, self.password)
            elif self.authentication_type == 'digest':
                session.auth = HTTPDigestAuth(self.user, self.password)
            elif self.authentication_type == 'token':
                session.auth = auth.HTTPTokenAuth(self.token)
            return session
        elif self.authentication_type == 'oauth2':
            params = {
                param.name: param.value
                for param in self.parameter_ids
            }
            if self.grant == 'password':
                return oauth.authenticate_password(
                    token_url=self.token_url,
                    client_key=self.client_key,
                    client_secret=self.client_secret,
                    username=self.user,
                    password=self.password,
                    include_client_id=self.include_client_key,
                    **params
                )
            elif self.grant == 'client_credentials':
                return oauth.authenticate_credentials(
                    token_url=self.token_url,
                    client_key=self.client_key,
                    client_secret=self.client_secret,
                    include_client_id=self.include_client_key,
                    **params
                )
        return Session()


class WebhookAuthenticationParameter(models.Model):
    _name = 'muk_webhooks.authentication.parameter'
    _description = 'Webhook Authentication Parameter'

    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------

    authentication_id = fields.Many2one(
        comodel_name='muk_webhooks.authentication',
        string='Authentication',
        ondelete='cascade',
        required=True
    )

    name = fields.Char(
        string='Parameter Key',
        required=True
    )

    value = fields.Char(
        string='Parameter Value',
        required=True
    )

    # ----------------------------------------------------------
    # Functions
    # ----------------------------------------------------------

    def name_get(self):
        return [
            (record.id, '%s = %s' % (record.name, record.value))
            for record in self
        ]
