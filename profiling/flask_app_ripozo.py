from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import Flask
from flask_ripozo import FlaskDispatcher
from ripozo import apimethod, ResourceBase, adapters

app = Flask(__name__)

class MyResource(ResourceBase):
    resource_name = 'my_resource'

    @apimethod(route='/hello/')
    def hello_world(cls, request):
        return cls(properties=dict(hello='world'))

dispatcher = FlaskDispatcher(app)
dispatcher.register_resources(MyResource)
dispatcher.register_adapters(adapters.HalAdapter)

if __name__ == '__main__':
    app.run(port=6000)
