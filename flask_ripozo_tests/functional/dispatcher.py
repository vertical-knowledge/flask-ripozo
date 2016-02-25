from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import unittest2

from flask import Flask
from ripozo import ResourceBase, apimethod, adapters, translate, fields
from six.moves import urllib
from webtest import TestApp

from flask_ripozo.dispatcher import FlaskDispatcher

app = Flask(__name__)
app.debug = True


id_field = fields.IntegerField('id', required=True)

class MyResource(ResourceBase):
    resource_name = 'resource'
    pks = 'id',

    @apimethod(methods=['GET'])
    @translate(fields=[id_field], validate=True)
    def retrieve(cls, request):
        return cls(properties={'method': 'retrieve', 'id': request.url_params.get('id')})

    @apimethod(methods=['POST'])
    @translate(fields=[id_field], validate=True)
    def create(cls, request):
        something = request.body_args.get('something')
        return cls(properties={'method': 'create', 'body': request.body_args})

    @apimethod(methods=['PATCH'])
    @translate(fields=[id_field], validate=True)
    def update(cls, request):
        return cls(properties={'method': 'update'})


dispatcher = FlaskDispatcher(app)
dispatcher.register_resources(MyResource)
dispatcher.register_adapters(adapters.SirenAdapter)


class TestDispatcher(unittest2.TestCase):
    def setUp(self):
        self.app = TestApp(app)

    def test_post_json(self):
        body = {'something': 'another'}
        expected = {
            'method': 'create',
            'body': body
        }
        resp = self.app.post('/resource/1/',
                             json.dumps(body),
                             headers={
                                 'Content-Type': b'application/json'
                             })
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.json['properties'], expected)

    def test_post_formencoded(self):
        body = {'something': 'another'}
        expected = {
            'method': 'create',
            'body': {'something': ['another']}
        }
        resp = self.app.post('/resource/1/',
                             urllib.parse.urlencode(body),
                             headers={
                                 'Content-Type': b'application/x-www-form-urlencoded'
                             })
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.json['properties'], expected)

    def test_post_json_no_content_type(self):
        body = {'something': 'another'}
        expected = {
            'method': 'create',
            'body': body
        }
        resp = self.app.post('/resource/1/',
                             json.dumps(body),
                             headers={
                                 'Content-Type': b'x-www-form-urlencoded'
                             })
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.json['properties'], expected)

    def test_retrieve_query_string(self):
        assert False

    def test_retrieve_no_query_string(self):
        resp = self.app.get('/resource/1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['properties'], {'method': 'retrieve', 'id': 1})

    def test_retrieve_content_type_set(self):
        resp = self.app.get('/resource/1/',
                            headers={'Content-Type': b'application/json'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['properties'], {'method': 'retrieve', 'id': 1})
