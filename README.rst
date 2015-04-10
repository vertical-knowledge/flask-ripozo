flask-ripozo
============

.. image:: https://travis-ci.org/vertical-knowledge/flask-ripozo.svg?branch=master&style=flat
    :target: https://travis-ci.org/vertical-knowledge/flask-ripozo

.. image:: https://coveralls.io/repos/vertical-knowledge/flask-ripozo/badge.svg?branch=master&style=flat
  :target: https://coveralls.io/r/vertical-knowledge/flask-ripozo?branch=master

.. image:: https://readthedocs.org/projects/flask-ripozo/badge/?version=latest&style=flat
    :target: https://flask-ripozo.readthedocs.org/
    :alt: Documentation Status

.. image:: https://pypip.in/version/flask-ripozo/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-ripozo/

.. image:: https://pypip.in/d/flask-ripozo/badge.png?style=flat
    :target: https://crate.io/packages/flask-ripozo/
    :alt: Number of PyPI downloads

.. image:: https://pypip.in/py_versions/flask-ripozo/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/flask-ripozo/

This package provides a dispatcher for ripozo so that you can
integrate ripozo with Flask.  As with all dispatchers it is simply
for getting the request arguments and appropriately routing them to
the various resources for handling.

Example
=======

This example describes a minimal flask-ripozo application.

.. code-block:: python

    from flask import Flask

    from flask_ripozo import FlaskDispatcher

    from ripozo.decorators import apimethod
    from ripozo.dispatcher.adapters import SirenAdapter, HalAdapter
    from ripozo.viewsets.resource_base import ResourceBase


    class HelloWorldViewset(ResourceBase):
        _resource_name = 'myresource'     # The name of the resource.  This will be appended to
                                          # the _namespace to complete the url.

        # The decorator indicates that the base url will be used
        # and that it will be registered for GET requests
        # a GET request to /api/myresource would be dispatched to this
        # method and handled here
        @apimethod(methods=['GET'])
        def hello(cls, request, *args, **kwargs):
            faked_response_properties = {'content': 'hello world'}
            return cls(properties=filters)

    # Create the flask application
    app = Flask(__name__)

    # Create the dispatcher
    dispatcher = FlaskDispatcher(app, base_url='/api')
    
    # Specify the valid response types
    dispatcher.register_adapters(SirenAdapter, HalAdapter)

    # This will register all of the apimethod decorated methods in
    # this class specified.  In this case it adds the /api/myresource GET
    # route to the application
    dispatcher.register_class_routes(HelloWorldViewset)

    if __name__ == '__main__':
        app.run() # Run the app
