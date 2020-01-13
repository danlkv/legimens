from legimens import Object, App

def setup_app(addr='127.0.0.1', port=8082):
    app = App(addr=addr, port=port)
    app.vars.title = 'Test'
    return app


def setup_app_nested(addr='127.0.0.1', port=8082):
    class User(Object):
        pass
    class Post(Object):
        pass
    u = User(name='John', age=30)
    u.posts = [Post(title='Legi'), Post(title='Megi')]

    app = App(addr=addr, port=port)
    app.vars.users = [u, User(name='Mohn', age=10)]
    app.vars.title = 'Test'
    return app

