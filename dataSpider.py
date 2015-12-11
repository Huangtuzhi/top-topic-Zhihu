#!/usr/bin/python
# -*- coding=utf-8 -*-

import requests
import re
from bs4 import BeautifulSoup
import string
from dataAccess import DataInfo


def get_xsrf_token(text):
    xsrf = re.search('(?<=name="_xsrf" value=")[^"]*(?="/)', text)
    if xsrf is None:
        return ''
    else:
        return xsrf.group(0)


def get_captcha(req):
    captcha = req.get('http://www.zhihu.com/captcha.gif', stream=True)
    print 'captcha status: '
    print captcha
    f = open('captcha.gif', 'wb')
    for line in captcha.iter_content(10):
        f.write(line)
    f.close()

    print 'Input the captcha'
    captcha_str = raw_input()
    return captcha_str


def get_login_cookies():
    url = 'http://www.zhihu.com'
    login_url = url + '/login/email'
    login_data = {
        '_xsrf': '',
        'password': 'password',
        'remember_me': 'true',
        'email': 'email@qq.com'
    }

    headers_base = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2',
        'Connection': 'keep-alive',
        'Host': 'www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
        'Referer': 'http://www.zhihu.com/',
    }

    req = requests.session()
    ret = req.get(url, headers=headers_base)
    xsrf = get_xsrf_token(ret.text)

    login_data['_xsrf'] = xsrf.encode('utf-8')

    captcha = get_captcha(req)
    login_data['captcha'] = captcha

    res = req.post(login_url, headers=headers_base, data=login_data)
    print 'login status: '
    print res.status_code

    local_cookies = res.cookies
    return req, local_cookies


def crawl_url(req, cookies, target_url):
    headers_base = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2',
        'Connection': 'keep-alive',
        'Host': 'www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
        'Referer': 'http://www.zhihu.com/',
    }

    ret = req.get(target_url, headers=headers_base, cookies=cookies)
    return ret.text


# def extract_topic(text):
#     pattern = re.compile('(?<=<a class="question_link" target="_blank" href="/question/).*">[^<>]*(?=</a>)')
#     topic = pattern.findall(text)
#     if topic is None:
#         return ''
#     else:
#         return topic


zhihu_people = set([])
zhihu_people_visited = set([])

def construct_people_db(req, local_cookies, text):
    global zhihu_people
    global zhihu_people_visited

    soup = BeautifulSoup(text)
    for one in soup(class_='author-link'):
        name = one.get('href').split('/')[-1]

        if name not in zhihu_people_visited:
            zhihu_people.add(name)

    for people in zhihu_people:
        zhihu_people_visited.add(people)
        zhihu_people.remove(people)

        with open('people_visited_db.txt', 'a') as people_visited_db:
            people_visited_db.write(people+'\n')

        another_homepage = 'https://www.zhihu.com/people/' + people

        # print another_homepage
        # write people to txt
        with open('people_db.txt', 'a') as people_db:
            people_db.write(people +'\n')

        another_text = crawl_url(req, local_cookies, another_homepage)
        construct_people_db(req, local_cookies, another_text)


zhihu_question = set([])

def construct_question_db(req, local_cookies):
    global zhihu_question
    question_db = open('question_db.txt', 'a')

    with open('people_visited_db.txt', 'r') as peoples:
        # 一次读入可能文件太大

        people = peoples.readline()
        while(people):
            homepage_url = "https://www.zhihu.com/people/" + people
            homepage_url = homepage_url.strip()
            homepage = crawl_url(req, local_cookies, homepage_url)
            soup = BeautifulSoup(homepage)
            for one in soup(class_='question_link'):
                question_id = one.get('href').split('/')[2]

                # 判断是否已经记录了这个 question_id
                if question_id not in zhihu_question:
                    zhihu_question.add(question_id)
                else:
                    continue

                question_title = one.string.encode('utf-8')
                print question_id, question_title
                question_db.write(question_id + ' ' + question_title + '\n')
            people = peoples.readline()

    peoples.close()
    question_db.close()


def get_topic_info(req, local_cookies):
    db = DataInfo()
    question_db = open('question_db.txt', 'r')

    question = question_db.readline()
    question_id = question.split(' ')[0]
    while(question_id):
        question_url = "https://www.zhihu.com/question/" + question_id + "/log"
        question_url = question_url.strip() #去除回车
        question_page = crawl_url(req, local_cookies, question_url)
        soup = BeautifulSoup(question_page)

        first_ask_time = soup.find_all("time")[-1].string
        # 可能会读不到数据
        follower_count = soup.find('div', class_='zh-question-followers-sidebar').find('strong').get_text() \
        if soup.find('div', class_='zh-question-followers-sidebar').find('strong') else 0

        db.add_data_to_mysql(first_ask_time, follower_count, question_id)
        print question_url, first_ask_time, follower_count

        question = question_db.readline()
        question_id = question.split(' ')[0]

    # 关闭连接
    db.close_mysql()


if __name__ == '__main__':

    # 获取登录 sesion 和 cookies，用来爬数据
    req, local_cookies = get_login_cookies()

    # 运行一次，用来抓取用户 ID，生成 people_db.txt
    # construct_people_db(req, local_cookies, text)

    # 抓取问题，生成 question_db.txt
    # construct_question_db(req, local_cookies)

    # 用 dataAccess 文件的类对 DB 操作，更新问题的提问时间和关注人数
    get_topic_info(req, local_cookies)