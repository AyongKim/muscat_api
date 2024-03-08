from flaskapp import app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True, debug=True, use_reloader=False)
