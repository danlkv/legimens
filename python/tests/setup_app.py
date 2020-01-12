from legimens import Object, App

def setup_app(addr='127.0.0.1', port=8082):
    class User(Object):
        def __init__(self, name, age):
            super().__init__()
            self.name = name
            self.age = age
    class Post(Object):
        def __init__(self, title, comments=[]):
            super().__init__()
            self.title = title
            self.comments = comments
    u = User(name='John', age=30)
    u.posts = [Post(title='Legi'), Post(title='Megi')]

    app = App(addr=addr, port=port)
    app.vars.users = [u, User(name='Mohn', age=10)]
    app.vars.title = 'Test'
    return app

