#!/usr/bin/python
# -*- coding:utf-8 -*-

from flask import Flask, jsonify
from flask import make_response
from dataAccess import DataInfo
from flask.ext.cors import CORS

# 提供给 js AJax 调用的 CGI

app = Flask(__name__)
CORS(app)

data = DataInfo()
topics = data.get_top_topic_these_days()

@app.route('/toptopic/api/topics', methods=['GET'])
def get_tasks():
    return jsonify({'topics': topics})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)