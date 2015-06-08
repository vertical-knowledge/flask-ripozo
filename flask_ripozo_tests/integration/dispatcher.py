from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import Flask, request

from flask_ripozo.dispatcher import get_request_query_body_args

import json
import unittest


class TestDispatcherFlaskIntegration(unittest.TestCase):
    def test_get_request_body_args(self):
        """
        Tests getting the request body args
        from a flask request object.
        """
        app = Flask('myapp')
        body = dict(x=1)
        with app.test_request_context('/', data=json.dumps(body), content_type='application/json'):
            q, b = get_request_query_body_args(request)
            self.assertDictEqual(b, body)

        with app.test_request_context('/', data=body):  # Form encoded
            q, b = get_request_query_body_args(request)
            self.assertDictEqual(b, dict(x=['1']))

    def test_get_request_body_args_nested(self):
        """
        Tests getting nested body args which seems to
        be handled slightly differnetly.
        """
        app = Flask('myapp')
        body = dict(x=1, y=dict(x=1))
        with app.test_request_context('/', data=json.dumps(body), content_type='application/json'):
            q, b = get_request_query_body_args(request)
            self.assertDictEqual(b, body)
