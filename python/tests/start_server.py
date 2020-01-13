from setup_app import setup_app_nested

if __name__ == '__main__':
    app = setup_app_nested()
    app.run_sync()
