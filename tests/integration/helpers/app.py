from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from flask import Flask

from flask_ripozo import FlaskDispatcher
from ripozo_tests.helpers.hello_world_viewset import HelloWorldViewset


app = Flask(__name__)

dispatcher = FlaskDispatcher(app)
dispatcher.register_class_routes(HelloWorldViewset)

@app.route('/')
def status():
    return 'running'

if __name__ == '__main__':
    app.run(debug=True)

