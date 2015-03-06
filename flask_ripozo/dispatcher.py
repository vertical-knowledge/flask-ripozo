from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from flask import request, jsonify
from ripozo.dispatch.dispatch_base import DispatcherBase
from ripozo.viewsets.request import RequestContainer
from werkzeug.routing import Rule, Map
import json


class FlaskDispatcher(DispatcherBase):
    """
    This is the actual dispatcher responsible for integrating
    ripozo with flask.  Pretty simple right?
    """

    def __init__(self, app):
        """
        Eventually these will be able to be registed to a blueprint.
        But for now it will probably break the routing by the adapters.

        :param flask.Flask|flask.Blueprint app:
        """
        self.app = app
        self.url_map = Map()
        self.function_for_endpoint = {}

    @property
    def base_url(self):
        return request.url_root

    def register_route(self, endpoint, endpoint_func=None, route=None, methods=None, **options):
        """
        Registers the endpoints on the flask application
        or blueprint.  It does so by using the add_url_rule on
        the blueprint/app.

        :param unicode endpoint: The name of the endpoint.  This is typically
            used in flask for reversing urls
        :param method endpoint_func: The actual function that is going to be called.
            This is generally going to be a @apimethod decorated, ResourceBase subclass
            method.
        :param unicode route:  The actual route that is going to be used.
        :param list methods: The http verbs that can be used with this endpoint
        :param dict options: The additional options to pass to the add_url_rule
        """
        # TODO why the None?
        self.app.add_url_rule(route, None, self.flask_dispatch, methods=methods, **options)
        self.url_map.add(Rule(route, endpoint=endpoint, methods=methods))
        self.function_for_endpoint[endpoint] = endpoint_func

    def flask_dispatch(self, **urlparams):
        """
        This is the method that dispatches the requests to endpoints
        that are part of the classes registered with this dispatcher instance.
        For example if a class Foo that has apimethods bar and baz in it and
        that class is registered on an instance of this dispatcher, then when a
        request that matches the route for bar or baz is caught by the flask app
        it is first directed here.  Here it is further directs it to the appropriate
        method (bar or baz) and an appropriate response is returned.

        This effectively translates Flask's interpretation of requests and responses
        into ripozo's interpretation of them.

        :param dict urlparams:  The url params that were passed by the flask
            app.  Typically these are going to be the _pks for the specified
            resource.
        :return: A response that the flask application can return.
        :rtype: flask.Response
        """
        urls = self.url_map.bind_to_environ(request.environ)
        request_args = request.args.copy()
        format_type = request_args.pop('format', 'siren')
        endpoint, args = urls.match()
        endpoint_func = self.function_for_endpoint[endpoint]
        r = RequestContainer(url_params=urlparams, query_args=request_args, body_args=request.form.copy(),
                             headers=request.headers)
        adapter = self.dispatch(endpoint_func, format_type, r)
        response = json.loads(adapter.formatted_body)
        return jsonify(response)
