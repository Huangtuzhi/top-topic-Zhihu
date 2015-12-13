#!/bin/bash

# 每天 23：00 抓取网站
crontab<<EOF
00 23 * * * /path/top-topic-Zhihu/dataSpider.py
EOF

