from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import Flask, Blueprint

from flask_ripozo.dispatcher import FlaskDispatcher, flask_dispatch_wrapper, get_request_query_body_args

from ripozo.exceptions import RestException

import json
import mock
import unittest2


class TestFlaskDispatcher(unittest2.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def get_mock_adapter_class(self):
        response_adapter = mock.MagicMock()
        response_adapter.formatted_body = 'some body'
        response_adapter.extra_headers = {'Content-Type': 'fake'}
        response_adapter.status_code = 600
        adapter_class = mock.Mock(return_value=response_adapter)
        adapter_class.formats = ['duh']
        adapter_class.format_exception = mock.Mock(return_value=('error', 'fake', 500,))
        return adapter_class

    def test_register_route(self):
        d = FlaskDispatcher(self.app)

        def fake():
            pass
        endpoint = 'someendpoint'
        values = dict(endpoint=endpoint, endpoint_func=fake,
                      route='/myresource', methods=['GET'])
        d.register_route(**values)
        self.assertIn(endpoint, self.app.url_map._rules_by_endpoint)
        rule = self.app.url_map._rules_by_endpoint[endpoint][0]
        self.assertIn('GET', rule.methods)
        self.assertEqual(rule.rule, '/myresource')
        self.assertEqual(endpoint, rule.endpoint)

        # They won't actually be the same function since it gets wrapped.
        self.assertEqual(self.app.view_functions[endpoint].__name__, fake.__name__)

    def test_flask_dispatch_wrapper(self):
        """
        Tests the wrapper to ensure that it properly calls the
        apimethod
        """
        adapter_class = self.get_mock_adapter_class()

        def fake(*args, **kwargs):
            return mock.Mock()

        d = FlaskDispatcher(self.app)
        d.register_adapters(adapter_class)
        view_func = flask_dispatch_wrapper(d, fake)
        self.assertEqual(view_func.__name__, fake.__name__)

        with self.app.test_request_context('/myresource'):
            response = view_func()
            self.assertEqual(response.content_type, 'fake')
            self.assertEqual(response.status_code, 600)
            self.assertEqual(response.data.decode('utf8'), 'some body')

    def test_flask_dispatch_wrapper_fail_restexception(self):
        """
        Tests the response when their is a failure in
        dispatching a request. In particular when a RestException
        is raised.
        """
        adapter_class = self.get_mock_adapter_class()

        def fake(*args, **kwargs):
            raise RestException

        d = FlaskDispatcher(self.app)
        d.register_adapters(adapter_class)
        view_func = flask_dispatch_wrapper(d, fake)
        self.assertEqual(view_func.__name__, fake.__name__)

        with self.app.test_request_context('/myresource'):
            response = view_func()
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.data.decode('utf8'), 'error')
            self.assertEqual(response.content_type, 'fake')

    def test_flask_dispatch_wrapper_fail(self):
        """
        Tests the response when their is a failure in
        dispatching a request that is not a RestException
        """
        adapter_class = self.get_mock_adapter_class()

        def fake(*args, **kwargs):
            raise Exception

        d = FlaskDispatcher(self.app)
        d.register_adapters(adapter_class)
        view_func = flask_dispatch_wrapper(d, fake)
        self.assertEqual(view_func.__name__, fake.__name__)

        with self.app.test_request_context('/myresource'):
            self.assertRaises(Exception, view_func)

    def test_base_url(self):
        """
        Tests that the base_url always returns the
        correct shit.
        """
        app = Flask('myapp')
        d = FlaskDispatcher(app)

        with app.test_request_context():
            self.assertEqual(d.base_url, 'http://localhost/')

        d = FlaskDispatcher(app, url_prefix='someprefix', auto_options_name='Options2')
        with app.test_request_context():
            self.assertEqual(d.base_url, 'http://localhost/someprefix')

    def test_blueprint_base_url(self):
        """
        Tests that dispatcher return the right shit
        when a blueprint is passed in.
        """
        with self.app.test_request_context():
            bp = Blueprint('name', __name__)
            d = FlaskDispatcher(bp)
            self.assertEqual(d.base_url, 'http://localhost/')

            d = FlaskDispatcher(bp, url_prefix='someprefix')
            self.assertEqual(d.base_url, 'http://localhost/someprefix')

            bp2 = Blueprint('name', __name__, url_prefix='another')
            d = FlaskDispatcher(bp2)
            self.assertEqual(d.base_url, 'http://localhost/another/')

            d = FlaskDispatcher(bp2, url_prefix='again')
            self.assertEqual(d.base_url, 'http://localhost/another/again')

    def test_get_request_query_body_args(self):
        """
        Tests the private get_request_query_body_args
        method.
        """
        query_args = dict(x=1)
        form = dict(x=2)
        mck = mock.Mock(args=query_args, form=form,
                        get_json=mock.Mock(return_value=None), headers={})
        q, b, h = get_request_query_body_args(mck)
        self.assertDictEqual(query_args, q)
        self.assertDictEqual(form, b)

        mck = mock.MagicMock(args=query_args, form=None,
                             get_json=mock.Mock(return_value=form), headers={})
        q, b, h = get_request_query_body_args(mck)
        self.assertDictEqual(query_args, q)
        self.assertDictEqual(form, b)

        mck = mock.MagicMock(args=query_args, form=None,
                             get_json=mock.Mock(return_value=None), data=json.dumps(form), headers={})
        q, b, h = get_request_query_body_args(mck)
        self.assertDictEqual(query_args, q)
        self.assertDictEqual({}, b)

    def test_register_route_invalid_options(self):
        """
        Tests registering a route with options not accepted
        by Flask.
        """
        app = Flask('myapp')
        d = FlaskDispatcher(app)

        def fake():
            return

        d.register_route('/ha', route='/ha', endpoint_func=fake, options=dict(invalid='option'))
        for rul in app.url_map._rules:
            if rul.endpoint == '/ha':
                break
        else:
            assert False
