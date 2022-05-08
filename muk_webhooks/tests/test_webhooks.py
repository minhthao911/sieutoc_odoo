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


import os
import json
import logging
import requests
import unittest

from odoo import _, http, tools, SUPERUSER_ID
from odoo.tests.common import TransactionCase
from odoo.addons.muk_webhooks.tools import encoder

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

WEBTESTER_TOKEN_URL = "https://webhook.site/token"
WEBTESTER_WEBHOOK_URL = "https://webhook.site/%s"
WEBTESTER_REQUESTS_URL = "https://webhook.site/token/%s/requests"

DISABLE_WEBHOOKS_TESTS = True
if os.environ.get('MUK_WEBHOOKS_ENABLE_TESTS'):
    DISABLE_WEBHOOKS_TESTS = False

DISABLE_WEBHOOKS_TEXT = "Skipped to avoid traffic on the test server."


class WebhookTestCase(TransactionCase):
    
    def setUp(self):
        super(WebhookTestCase, self).setUp()
        self.model_model = self.env['ir.model']
        self.model_fields = self.env['ir.model.fields']
        self.action = self.env['ir.actions.server']
        self.authentication = self.env['muk_webhooks.authentication']
        self.model_partner = self.model_model.search([('model', '=', 'res.partner')], limit=1)
        field_domain = [('model_id', '=', self.model_partner.id), ('name', '=', 'name')]
        self.field_partner_name = self.model_fields.search(field_domain, limit=1)
        self.uuid = requests.post(WEBTESTER_TOKEN_URL).json().get('uuid')
    
    def get_requests(self, uuid):
        return requests.get(WEBTESTER_REQUESTS_URL % uuid).json()
    
    @unittest.skipIf(DISABLE_WEBHOOKS_TESTS, DISABLE_WEBHOOKS_TEXT)
    def test_webhook_simple(self):
        webhook = self.action.create({
            'name': "Webhook Test Simple",
            'state': 'request',
            'model_id': self.model_partner.id,
            'request_field_ids': [(6, 0, [self.field_partner_name.id])],
            'request_address': WEBTESTER_WEBHOOK_URL % self.uuid
        })
        webhook.run()
        webhook_requests = self.get_requests(self.uuid)
        self.assertTrue(webhook_requests.get('total') == 1)
        webhook_payload = webhook_requests.get('data')[0]['request']
        self.assertEqual(webhook_requests.get('data')[0]['method'], 'POST')
        self.assertEqual(webhook_payload.get('name'), "Webhook Test Simple")
        self.assertEqual(webhook_payload.get('model'), 'res.partner')
    
    @unittest.skipIf(DISABLE_WEBHOOKS_TESTS, DISABLE_WEBHOOKS_TEXT)
    def test_webhook_method(self):
        webhook = self.action.create({
            'name': "Webhook Test Method",
            'state': 'request',
            'model_id': self.model_partner.id,
            'request_method': 'GET',
            'request_field_ids': [(6, 0, [self.field_partner_name.id])],
            'request_address': WEBTESTER_WEBHOOK_URL % self.uuid
        })
        webhook.run()
        webhook_requests = self.get_requests(self.uuid)
        self.assertTrue(webhook_requests.get('total') == 1)
        self.assertEqual(webhook_requests.get('data')[0]['method'], 'GET')
    
    @unittest.skipIf(DISABLE_WEBHOOKS_TESTS, DISABLE_WEBHOOKS_TEXT)
    def test_webhook_headers(self):
        webhook = self.action.create({
            'name': "Webhook Test Headers",
            'state': 'request',
            'model_id': self.model_partner.id,
            'request_method': 'GET',
            'request_field_ids': [(6, 0, [self.field_partner_name.id])],
            'request_headers_value_ids': [(0, 0, {'name': 'Content-Type', 'value': 'application/json'})],
            'request_address': WEBTESTER_WEBHOOK_URL % self.uuid
        })
        webhook.run()
        webhook_requests = self.get_requests(self.uuid)
        self.assertTrue(webhook_requests.get('total') == 1)
        self.assertEqual(webhook_requests.get('data')[0]['method'], 'GET')
    
    @unittest.skipIf(DISABLE_WEBHOOKS_TESTS, DISABLE_WEBHOOKS_TEXT)
    def test_webhook_payload(self):
        webhook = self.action.create({
            'name': "Webhook Test Payload",
            'state': 'request',
            'model_id': self.model_partner.id,
            'request_field_ids': [(6, 0, [self.field_partner_name.id])],
            'request_address': WEBTESTER_WEBHOOK_URL % self.uuid,
            'request_payload_code': "content = json.dumps(model.search([], limit=1).read(fields=['display_name']))",
            'request_adapt_payload': True,
        })
        records = self.env['res.partner'].search([], limit=1).read(fields=['display_name'])
        tester = json.dumps(records, cls=encoder.RequestEncoder)
        webhook.run()
        webhook_requests = self.get_requests(self.uuid)
        self.assertTrue(webhook_requests.get('total') == 1)
        webhook_payload = webhook_requests.get('data')[0]['request']
        self.assertEqual(webhook_payload.get('content'), tester)
    
    @unittest.skipIf(DISABLE_WEBHOOKS_TESTS, DISABLE_WEBHOOKS_TEXT)
    def test_webhook_process(self):
        webhook = self.action.create({
            'name': "Webhook Test Process",
            'state': 'request',
            'model_id': self.model_partner.id,
            'request_field_ids': [(6, 0, [self.field_partner_name.id])],
            'request_address': WEBTESTER_WEBHOOK_URL % self.uuid,
            'request_process_response_code': "log('%s' + '-' + str(response.status_code))" % self.uuid,
            'request_adapt_payload': True,
        })
        webhook.run()
        webhook_requests = self.get_requests(self.uuid)
        self.assertTrue(webhook_requests.get('total') == 1)
    
    @unittest.skipIf(DISABLE_WEBHOOKS_TESTS, DISABLE_WEBHOOKS_TEXT)
    def test_webhook_authentication(self):
        authentication = self.authentication.create({
            'name': "Webhook Test Basic",
            'authentication_type': 'base',
            'user': 'base',
            'password': 'base'
        })
        webhook = self.action.create({
            'name': "Webhook Test Basic",
            'state': 'request',
            'model_id': self.model_partner.id,
            'request_field_ids': [(6, 0, [self.field_partner_name.id])],
            'request_address': WEBTESTER_WEBHOOK_URL % self.uuid,
            'request_authentication_id': authentication.id,
        })
        webhook.run()
        webhook_requests = self.get_requests(self.uuid)
        self.assertTrue(webhook_requests.get('total') == 1)
        webhook_headers = webhook_requests.get('data')[0]['headers']
        self.assertTrue(webhook_headers.get('authorization')[0].startswith('Basic'))
