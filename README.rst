flask-ripozo
============

.. image:: https://travis-ci.org/vertical-knowledge/flask-ripozo.svg?branch=master
    :target: https://travis-ci.org/vertical-knowledge/flask-ripozo

.. image:: https://readthedocs.org/projects/flask-ripozo/badge/?version=latest
    :target: https://flask-ripozo.readthedocs.org/
    :alt: Documentation Status

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
    from ripozo.viewsets.resource_base import ResourceBase

    from ripozo_tests.helpers.inmemory_manager import InMemoryManager


    class Manager(InMemoryManager):
        # This is just for test purposes.
        # In real applications you would want to use
        # something like ripozo-sqlalchemy to actually
        # manage your models.  Also in future
        # versions of ripozo a Manager class will
        # not be required for a Resource class
        model = 'SomeModel'
        _model_name = 'modelname'


    class HelloWorldViewset(ResourceBase):
        _namespace = '/api/'              # The base url of the resource
        _manager = Manager                # This should not be required in future versions of ripozo
        _resource_name = 'myresource'     # The name of the resource.  This will be appended to
                                          # the _namespace to complete the url.

        _fields = ['content']             # Necessary because the _manager is necessary.  Will
                                          # be removed in future versions

        # The decorator indicates that the base url will be used
        # and that it will be registered for GET requests
        # a GET request to /api/myresource would be dispatched to this
        # method and handled here
        @apimethod(methods=['GET'])
        def hello(cls, primary_keys, filters, values, *args, **kwargs):
            faked_response_properties = {'content': 'hello world'}
            return cls(properties=filters)


    app = Flask(__name__)  # Create the flask application

    # Create the dispatcher
    # A flask blueprint could also be used here.s
    dispatcher = FlaskDispatcher(app)

    # This will register all of the apimethod decorated methods in
    # this class specified.  In this case it adds the /api/myresource GET
    # route to the application
    dispatcher.register_class_routes(HelloWorldViewset)

    if __name__ == '__main__':
        app.run() # Run the app