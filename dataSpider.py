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
        'password': 'your_password',
        'remember_me': 'true',
        'email': 'your_email'
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


# V1 版本，用 set 存储中间数据
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


# V2 版本，用数据库模拟 set 存储中间数据
dbObject = DataInfo()
def construct_people_db_v2(req, local_cookies, text):
    global dbObject
    soup = BeautifulSoup(text)
    for one in soup(class_='author-link'):
        name = one.get('href').split('/')[-1]

        if not dbObject.is_people_visited(name):
            dbObject.add_to_people_db(name)

    all_people = dbObject.get_all_in_people_db()
    for people in all_people:
        dbObject.add_to_people_visited_db(people)
        dbObject.remove_from_people_db(people)

        another_homepage = 'https://www.zhihu.com/people/' + people
        another_text = crawl_url(req, local_cookies, another_homepage)
        construct_people_db_v2(req, local_cookies, another_text)

    dbObject.close_mysql()


# V1 版本，由 people 生成 question
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


# V1 版本, 由 question 信息去网络上爬提问时间，关注者信息，补充 question 数据
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
        # print question_url, first_ask_time, follower_count

        question = question_db.readline()
        question_id = question.split(' ')[0]

    # 关闭连接
    db.close_mysql()


# V2 版本，由 people 生成 question。直接操作数据库，不进行写文件操作。
def convert_from_people_to_question(req, local_cookies):
    dbObject = DataInfo()
    all_people = dbObject.get_all_in_people_merged_db()

    for people in all_people:
        homepage_url = "https://www.zhihu.com/people/" + people
        homepage = crawl_url(req, local_cookies, homepage_url)
        soup = BeautifulSoup(homepage)
        for one in soup(class_='question_link'):
            question_id = one.get('href').split('/')[2]

            # 判断 DB 是否已经有了这个 question_id，有了则重新获取别的
            if dbObject.is_question_visited(question_id):
                continue

            question_title = one.string.encode('utf-8')

            question_url = "https://www.zhihu.com/question/" + question_id + "/log"
            question_page = crawl_url(req, local_cookies, question_url)
            page_soup = BeautifulSoup(question_page)
            first_ask_time = page_soup.find_all("time")[-1].string if page_soup.find_all("time") else '2000-00-00'
            # 由于“服务器提出了一个问题”，可能会读不到数据
            if (page_soup.find('div', class_='zh-question-followers-sidebar') == None):
                continue;
            follower_count = page_soup.find('div', class_='zh-question-followers-sidebar').find('strong').get_text() \
                if page_soup.find('div', class_='zh-question-followers-sidebar').find('strong') else 0

            dbObject.add_data_to_question_db(question_id, question_title, first_ask_time, follower_count)
            print question_id, question_title, first_ask_time, follower_count

    dbObject.close_mysql()

if __name__ == '__main__':

    # 获取登录 sesion 和 cookies，用来爬数据
    req, local_cookies = get_login_cookies()
    # text = crawl_url(req, local_cookies, 'https://www.zhihu.com/people/titushuang')

    # V1 版本。运行一次，用来抓取用户 ID，生成 people_db.txt
    # construct_people_db(req, local_cookies, text)

    # V1 版本。抓取问题，生成 question_db.txt
    # construct_question_db(req, local_cookies)

    # V1 版本。用 dataAccess 文件的类对 DB 操作，更新问题的提问时间和关注人数
    # get_topic_info(req, local_cookies)

    # V2 版本构造 people 的数据库
    # construct_people_db_v2(req, local_cookies, text)

    # V2 版本，由 people 生成 question
    convert_from_people_to_question(req, local_cookies)

