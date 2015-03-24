from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import request, Response

from ripozo.dispatch.dispatch_base import DispatcherBase
from ripozo.utilities import join_url_parts
from ripozo.viewsets.request import RequestContainer

from werkzeug.routing import Rule, Map


class FlaskDispatcher(DispatcherBase):
    """
    This is the actual dispatcher responsible for integrating
    ripozo with flask.  Pretty simple right?
    """

    def __init__(self, app, url_prefix=''):
        """
        Eventually these will be able to be registed to a blueprint.
        But for now it will probably break the routing by the adapters.

        :param flask.Flask app: The flask app that is responsible for
            handling the web application.
        :param unicode url_prefix: The url prefix will be prepended to
            every route that is registered on this dispatcher.  It is
            helpful if, for example, you want to expose your api
            on the '/api' path.
        """
        self.app = app
        self.url_map = Map()
        self.function_for_endpoint = {}
        self.url_prefix = url_prefix

    @property
    def base_url(self):
        # TODO this is a temp fix
        # It will break with multiple dispatchers working together.
        return join_url_parts(request.url_root, self.url_prefix)

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
        # TODO this is a temp fix
        # It will break with multiple dispatchers working together.
        route = join_url_parts(self.url_prefix, route)
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
        request_args = dict(request.args)
        endpoint, args = urls.match(method=request.method)
        endpoint_func = self.function_for_endpoint[endpoint]
        r = RequestContainer(url_params=urlparams, query_args=request_args, body_args=dict(request.form),
                             headers=request.headers)
        adapter = self.dispatch(endpoint_func, request.content_type, r)
        response = Response(response=adapter.formatted_body, headers=adapter.extra_headers, content_type=adapter.extra_headers['Content-Type'])
        return adapter.formatted_body
