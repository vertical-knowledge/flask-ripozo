*********************
flask-ripozo Tutorial
*********************

In this tutorial we will create a todo list
application.  We will be using,
flask-ripozo (Which include Flask of course), ripozo-sqlalchemy
(Which uses SQLAlchemy) and Flask-User for authentication.

The first step is to install the required dependencies.  I
highly recommend setting this up in a virtual environment of
course.

.. code-block:: bash

    pip install flask-ripozo, ripozo-sqlalchemy, Flask-SQLAlchemy

Setting up the Flask application
================================

The first step is to install the required dependencies.  I
highly recommend setting this up in a virtual environment of
course.

.. code-block:: bash

    pip install flask-ripozo, ripozo-sqlalchemy, Flask-SQLAlchemy

Next we'll need to create our application.

.. code-block:: python

    from flask import Flask
    from flask.ext.sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ripozo_example.db'
    db = SQLAlchemy(app)

Then we will setup our models.

.. code-block:: python

    from sqlalchemy.orm import relationship

    class TaskBoard(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        tasks = relationship('Task', backref='task_board')
        title = db.Column(db.String(50), nullable=False)

    class Task(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        task_board_id = db.Column(db.Integer, db.ForeignKey('task_board.id'), nullable=False)
        title = db.Column(db.String(50), nullable=False)
        description = db.Column(db.Text, nullable=False)
        completed = db.Column(db.Boolean, default=False)

    db.create_all()


Now that we have our non-ripozo aspect set up we
are ready to start building a RESTful API!

Resources
=========

Resources are the core of ripozo.  These are common
across all manager and dispatcher packages.  This means,
assuming that the application was developed well, you could
reuse the resources in Django or mix them in with the cassandra
manager.

.. code-block:: python

    from ripozo import restmixins, ListRelationship, Relationship

    class TaskBoardResource(restmixins.CRUDL):
        manager = TaskBoardManager(session_handler)
        resource_name = 'taskboard'
        pks = ('id',)
        _relationships = (
            ListRelationship('tasks', relation='TaskResource'),
        )

        @apimethod(route='/addtask', methods=['POST'])
        def add_task(cls, request):
            body_args = request.body_args
            body_args['task_board_id'] = request.get('id')
            request.body_args = body_args
            return TaskResource.create(request)

    class TaskResource(restmixins.CRUD):
        manager = TaskManager(session_handler)
        resource_name = 'task'
        pks = ('id',)
        _relationships = (
            Relationship('task_board', property_map=dict(task_board_id='id'), relation='TaskBoardResource'),
        )


We now have a reusable core to our RESTful API.  This is reusable across
various web frameworks, databases (you will have to change the manager),
or REST protocol.

Managers
========

The first step in setting up our RESTful application
is to define our managers.  Managers are responsible
for maintaining state in the application.  They are
the common interface for interacting with databases.

Defining managers is actually very simple:

.. code-block:: python

    from ripozo_sqlalchemy import AlchemyManager

    # This is the most basic session handler.
    # It simply passes the db.session object and
    # lets Flask-SQLAlchemy handle the rest.
    session_handler = SessionHandler(db.session)

    class TaskBoardManager(AlchemyManager):
        _fields = ('id', 'title', 'tasks.id',)
        _list_fields = ('id', 'title',)
        _update_fields = ('title',)
        model = TaskBoard
        paginate_by = 10

    class TaskManager(AlchemyManager):
        _fields = ('id', 'task_board_id', 'title', 'description', 'completed',)
        model = Task
        paginate_by = 20

And that's it.  This provided a common interface for
creating, updating, deleting, and retrieving both the
TaskBoard and Task.  These allow us to quickly implement
the common CRUD+L actions using the builtin Rest mixins.

Dispatchers
===========

Dispatchers are responsible for registering
our resources with the flask application.
This allows us to actually call our endpoints.

.. code-block:: python

    from flask_ripozo import FlaskDispatcher
    from ripozo import adapters

    dispatcher = FlaskDispatcher(app, url_prefix='/api')
    dispatcher.register_resources(TaskBoardResourceList, TaskBoardResource, TaskResource)
    dispatcher.register_adapters(adapters.SirenAdapter, adapters.HalAdapter)

We now have a functioning RESTful api that serves both
Siren and HAL protocls.

To start up this application, we just need to run:

.. code-block:: python

    app.run()

Using the api
=============

We'll be using pypermedia to access the
api.  It makes it extremely easy to use
a SIREN based protocol.  You could use
HAL protocol if you preferred by prepending
that to your accept-types.

.. code-block:: bash

    pip install pypermedia

First we'll create a task board

.. code-block:: python

    >>> siren_client = HypermediaClient.connect('http://127.0.0.1:5000/api/taskboard/', request_factory=requests.Request)
    >>> task_board_list = siren_client.retrieve_list()
    >>> created = task_board_list.create(title='My First Board')
    >>> retrieve = created.retrieve()
    >>> print(created.title)
    'My First Board'
    >>> print(created.id)
    5

Now we can update the board's title.

.. code-block:: python

    >>> updated = retrieve.update(title='My Updated Board')
    >>> print(updated.title)
    'My Updated Board'

Of course we can't have a task board without any tasks!

.. code-block:: python

    >>> new_task = updated.add_task(title='My first task', description='I need to do something')
    >>> print(new_task.title)
    'My first task'
    >>> print(new_task.description)
    'I need to do something'
    >>> print(new_task.completed)
    False

We can now get this task from the task board itself.

.. code-block:: python

    >>> task_board = retrieve.retrieve()
    >>> task = next(task_board.get_entities('tasks'))
    >>> print(task.description)
    'I need to do something'
    >>> print(task.completed)
    False

Well I guess we did something.  We'll update the task.

.. code-block:: python

    >>> task = task.update(completed=True)
    >>> print(task.completed)
    True

And we can get the board this task belonds to by getting the task_board entity

.. code-block:: python

    >>> parent_board = next(task.get_entities('task_board'))
    >>> print(parent_board.title)
    My Updated Board

That task is dumb.  Let's delete it.

.. code-block:: python

    >>> deleted = task.delete()
    >>> original_task = task.retrieve()
    >>> print(original_task)
    None


