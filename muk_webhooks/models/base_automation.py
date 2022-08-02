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

from requests import Request, Session
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from requests.exceptions import RequestException

from odoo import api, models, fields, tools, _
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.addons.muk_webhooks.tools import auth, oauth, encoder

_logger = logging.getLogger(__name__)


class BaseAutomation(models.Model):
    
    _inherit = 'base.automation'

    #----------------------------------------------------------
    # Actions
    #----------------------------------------------------------
    
    def action_open_report(self):
        return self.action_server_id.action_open_report()

    def action_open_preview(self):
        self.ensure_one()
        return {
            'name': _("Preview Automation"),
            'type': 'ir.actions.act_window',
            'res_model': 'muk_webhooks.preview',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'preview_domain': safe_eval(
                    self.filter_domain or '[]',
                    self._get_eval_context()
                ),
                'default_action_id': self.action_server_id.id
            }
        }
    