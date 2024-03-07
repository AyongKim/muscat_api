from flaskapp import app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1001, threaded=True, debug=True, use_reloader=False)
