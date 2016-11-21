from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import request, Response

from functools import wraps

from ripozo.dispatch_base import DispatcherBase
from ripozo.exceptions import RestException
from ripozo.utilities import join_url_parts
from ripozo.resources.request import RequestContainer

from werkzeug.routing import Map

import logging
import six

_logger = logging.getLogger(__name__)


class _CaseInsentiveDict(dict):
    def __setitem__(self, key, value):
        super(_CaseInsentiveDict, self).__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super(_CaseInsentiveDict, self).__getitem__(key.lower())


def exception_handler(dispatcher, accepted_mimetypes, exc):
    """
    Responsible for handling exceptions in the project.
    This catches any RestException (from ripozo.exceptions)
    and calls the format_exception class method on the adapter
    class.  It will appropriately set the status_code, response,
    and content type for the exception.

    :param FlaskDispatcher dispatcher: A FlaskDispatcher instance
        used to format the exception
    :param list accepted_mimetypes: A list of the accepted mimetypes
        for the client.
    :param Exception exc: The exception that was raised.
    :return: A flask Response object.
    :rtype: flask.Response
    """
    if isinstance(exc, RestException):
        adapter_klass = dispatcher.get_adapter_for_type(accepted_mimetypes)
        response, content_type, status_code = adapter_klass.format_exception(exc)
        return Response(response=response, content_type=content_type, status=status_code)
    raise exc


def get_request_query_body_args(request_obj):
    """
    Gets the request query args and the
    body arguments.  It gets the query_args from
    the flask request.args and transforms it from an
    ImmutableMultiDict to a dict.  It attempts to retrieve
    json for the body first.  If it doesn't find any it
    looks at the form otherwise it returns an empty dictionary.
    The body is also transformed from an ImmutableMultiDict to
    a builtin dict.

    :param flask.Request request_obj: A Flask request object.
    :return: A tuple of the appropriately formatted query
        args, body args, and headers
    :rtype: (dict, dict, dict)
    """
    query_args = dict(request_obj.args)
    body = dict(
        request_obj.get_json(force=True, silent=True) or
        request_obj.form or
        {}
    )

    # Make a copy of the headers
    headers = _CaseInsentiveDict()
    for key, value in six.iteritems(request_obj.headers):
        headers[key] = value
    return query_args, body, headers


class FlaskDispatcher(DispatcherBase):
    """
    This is the actual dispatcher responsible for integrating
    ripozo with flask.  Pretty simple right?
    """

    def __init__(self, app, url_prefix='', error_handler=exception_handler,
                 argument_getter=get_request_query_body_args, **kwargs):
        """
        Initialize the adapter.  The app can actually be either a flask.Flask
        instance or a flask.Blueprint instance.

        :param flask.Flask|flask.Blueprint app: The flask app that is responsible for
            handling the web application.
        :param unicode url_prefix: The url prefix will be prepended to
            every route that is registered on this dispatcher.  It is
            helpful if, for example, you want to expose your api
            on the '/api' path.
        :param function error_handler: A function that takes a dispatcher,
            accepted_mimetypes, and exception that handles error responses.
            It should return a flask.Response instance.
        :param function argument_getter:  The function responsible for
            getting the query/body arguments from the Flask Request as a
            tuple. This function should return (dict, dict,) with the first
            as the query args and the second as the request body args.
        """
        self.app = app
        self.url_map = Map()
        self.function_for_endpoint = {}
        if url_prefix and not url_prefix.startswith('/'):
            url_prefix = '/{0}'.format(url_prefix)
        self.url_prefix = url_prefix
        self.error_handler = error_handler
        self.argument_getter = argument_getter
        super(FlaskDispatcher, self).__init__(**kwargs)

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
                              view_func=flask_dispatch_wrapper(self, endpoint_func, self.argument_getter),
                              methods=methods, **options)


def flask_dispatch_wrapper(dispatcher, f, argument_getter=get_request_query_body_args):
    """
    A decorator for wrapping the apimethods provided to the
    dispatcher.  The actual wrapper performs that actual
    construction of the RequestContainer, determines the appropriate
    adapter to use, dispatches the method, and passes errors to
    the dispatcher.error_handler method. Finally, it will return
    a flask.Response instance except in the case of an exception
    raised by the dispatch.error_handler (typically error_handlers
    only handle certain sets of exceptions).

    :param FlaskDispatcher dispatcher:  The dispatcher that is
        created this.
    :param function f:  The apimethod to wrap.
    :param function argument_getter:  The function that takes a flask
        Request object and uses it to get the query arguments and the
        body arguments as a tuple.
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
        request_args, body_args, headers = argument_getter(request)
        ripozo_request = RequestContainer(url_params=urlparams,
                                          query_args=request_args,
                                          body_args=body_args,
                                          headers=headers)
        accepted_mimetypes = [accept[0] for accept in request.accept_mimetypes]
        try:
            adapter = dispatcher.dispatch(f, accepted_mimetypes, ripozo_request)
        except Exception as e:
            _logger.exception(e)
            return dispatcher.error_handler(dispatcher, accepted_mimetypes, e)

        return Response(response=adapter.formatted_body, headers=adapter.extra_headers,
                        content_type=adapter.extra_headers['Content-Type'], status=adapter.status_code)
    return flask_dispatch
