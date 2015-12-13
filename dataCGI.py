#!/usr/bin/python
# -*- coding:utf-8 -*-

from flask import Flask, jsonify
from flask import make_response
from dataAccess import DataInfo
from flask.ext.cors import CORS
import time

# 提供给 js AJax 调用的 CGI

app = Flask(__name__)
CORS(app)

@app.route('/toptopic/api/topics/<int:look_days>', methods=['GET'])
def get_tasks(look_days):
    print 'start', time.time()
    dbObject = DataInfo()
    topics = dbObject.get_top_topic_these_days(look_days)
    dbObject.close_mysql()
    result = jsonify({'topics': topics})
    print 'end', time.time()
    return result

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='your_ip',port=5000, debug=True, threaded=True)