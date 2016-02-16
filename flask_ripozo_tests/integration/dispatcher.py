from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import Flask, request

from flask_ripozo.dispatcher import get_request_query_body_args

import json
import unittest2


class TestDispatcherFlaskIntegration(unittest2.TestCase):
    def test_get_request_body_args(self):
        """
        Tests getting the request body args
        from a flask request object.
        """
        app = Flask('myapp')
        body = dict(x=1)
        with app.test_request_context('/', data=json.dumps(body), content_type='application/json'):
            q, b, headers = get_request_query_body_args(request)
            self.assertDictEqual(b, body)

        with app.test_request_context('/', data=body):  # Form encoded
            q, b, headers = get_request_query_body_args(request)
            self.assertDictEqual(b, dict(x=['1']))

    def test_get_request_body_args_nested(self):
        """
        Tests getting nested body args which seems to
        be handled slightly differnetly.
        """
        app = Flask('myapp')
        body = dict(x=1, y=dict(x=1))
        with app.test_request_context('/', data=json.dumps(body), content_type='application/json'):
            q, b, headers = get_request_query_body_args(request)
            self.assertDictEqual(b, body)

    def test_headers_copyable(self):
        """
        Tests that the headers returned from get_request_query_body_args
        appropriately returns the headers as a dictionary that can be copied
        """
        app = Flask('myapp')
        with app.test_request_context('/'):
            q, b, headers = get_request_query_body_args(request)
        headers2 = headers.copy()
        self.assertDictEqual(headers, headers2)
