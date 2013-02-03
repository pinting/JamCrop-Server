from gaesessions import SessionMiddleware
def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app, cookie_key = "yRke2ilYlQh5tgUy48Pz50N4w8ON7EUu")
    return app