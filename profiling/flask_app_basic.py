from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/my_resource/hello/')
def hello():
    return jsonify({
        "entities": [],
        "class": ["my_resource"],
        "links": [
            {
                "href": "http://127.0.0.1:6000/my_resource",
                "rel": ["self"]
            }
        ],
        "actions": [
            {
                "fields": [],
                "href": "http://127.0.0.1:6000/my_resource/hello/",
                "title": "Hello World",
                "method": "GET",
                "name": "hello_world"
            }
        ],
        "properties": {
            "hello": "world"
        }
    })

if __name__ == '__main__':
    app.run(port=6000)