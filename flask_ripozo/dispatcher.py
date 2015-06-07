from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import request, Response

from functools import wraps

from ripozo.dispatch.dispatch_base import DispatcherBase
from ripozo.exceptions import RestException
from ripozo.utilities import join_url_parts
from ripozo.viewsets.request import RequestContainer

from werkzeug.routing import Map

import json
import six


def exception_handler(dispatcher, accepted_mimetypes, exc):
    """
    Responsible for handling exceptions in the project.

    :param FlaskDispatcher dispatcher: A FlaskDispatcher instance
        used to format the exception
    :param list accepted_mimetypes: A list of the accepted mimetypes
        for the client.
    :param Exception exc: The exception that was raised.
    :return: A flask Response object.
    :rtype: Response
    """
    if isinstance(exc, RestException):
        adapter_klass = dispatcher.get_adapter_for_type(accepted_mimetypes)
        response, content_type, status_code = adapter_klass.format_exception(exc)
        return Response(response=response, content_type=content_type, status=status_code)
    raise exc


class FlaskDispatcher(DispatcherBase):
    """
    This is the actual dispatcher responsible for integrating
    ripozo with flask.  Pretty simple right?
    """

    def __init__(self, app, url_prefix='', error_handler=exception_handler):
        """
        Eventually these will be able to be registed to a blueprint.
        But for now it will probably break the routing by the adapters.

        :param flask.Flask|flask.Blueprint app: The flask app that is responsible for
            handling the web application.
        :param unicode url_prefix: The url prefix will be prepended to
            every route that is registered on this dispatcher.  It is
            helpful if, for example, you want to expose your api
            on the '/api' path.
        :param function error_handler: A function that takes a dispatcher,
            accepted_mimetypes, and exception that handles error responses.
        """
        self.app = app
        self.url_map = Map()
        self.function_for_endpoint = {}
        self.url_prefix = url_prefix
        self.error_handler = error_handler

    @property
    def base_url(self):
        """
        :return: The base_url for this adapter.  It simply joins
            the provided base_url in the __init__ method and
            joins it with the ``request.url_root``.  If this
            app provided is actually a blueprint, it will
            return join the blueprints url_prefix in between
        :rtype: unicode
        """
        if getattr(self.app, 'url_prefix', None):
            return join_url_parts(request.url_root, self.app.url_prefix, self.url_prefix)
        return join_url_parts(request.url_root, self.url_prefix)

    def register_route(self, endpoint, endpoint_func=None, route=None, methods=None, **options):
        """
        Registers the endpoints on the flask application
        or blueprint.  It does so by using the add_url_rule on
        the blueprint/app.  It wraps the endpoint_func with the
        ``flask_dispatch_wrapper`` which returns an updated function.
        This function appropriately sets the RequestContainer object
        before passing it to the apimethod.

        :param unicode endpoint: The name of the endpoint.  This is typically
            used in flask for reversing urls
        :param method endpoint_func: The actual function that is going to be called.
            This is generally going to be a @apimethod decorated, ResourceBase subclass
            method.
        :param unicode route:  The actual route that is going to be used.
        :param list methods: The http verbs that can be used with this endpoint
        :param dict options: The additional options to pass to the add_url_rule
        """
        valid_flask_options = ('defaults', 'subdomain', 'methods', 'build_only',
                               'endpoint', 'strict_slashes', 'redirect_to',
                               'alias', 'host')
        route = join_url_parts(self.url_prefix, route)

        # Remove invalid flask options.
        options_copy = options.copy()
        for key, value in six.iteritems(options_copy):
            if key not in valid_flask_options:
                options.pop(key, None)
        self.app.add_url_rule(route, endpoint=endpoint,
                              view_func=flask_dispatch_wrapper(self, endpoint_func),
                              methods=methods, **options)


def flask_dispatch_wrapper(dispatcher, f):
    """
    A decorator for wrapping the apimethods provided to the
    dispatcher.
    """

    @wraps(f)
    def flask_dispatch(**urlparams):
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
        request_args, body_args = _get_request_query_body_args(request)
        r = RequestContainer(url_params=urlparams, query_args=request_args, body_args=body_args,
                             headers=request.headers)
        accepted_mimetypes = request.accept_mimetypes
        try:
            adapter = dispatcher.dispatch(f, accepted_mimetypes, r)
        except Exception as e:
            return dispatcher.error_handler(dispatcher, accepted_mimetypes, e)

        return Response(response=adapter.formatted_body, headers=adapter.extra_headers,
                        content_type=adapter.extra_headers['Content-Type'], status=adapter.status_code)
    return flask_dispatch


def _get_request_query_body_args(request_obj):
    """
    Gets the request query args and the
    body arguments.

    :param Request request_obj: A Flask request object.
    :return: A tuple of the appropriately formatted query args and body args
    :rtype: dict, dict
    """
    query_args = dict(request_obj.args)
    # TODO What the fuck.
    if request_obj.form:
        return query_args, dict(request_obj.form)
    elif request_obj.json:
        return query_args, dict(request_obj.json)
    elif request_obj.data:
        return query_args, json.loads(request_obj.data)
    return query_args, {}
