#!/usr/bin/python
# -*- coding:utf-8 -*-

import MySQLdb
import MySQLdb.cursors
from datetime import *
import time


class DataInfo(object):
    def __init__(self):
        self.db = MySQLdb.connect("localhost", "root", "XXXXX", "top_topic_zhihu",
                                  cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
        self.cursor = self.db.cursor()

    def close_mysql(self):
        self.db.close()

    # 建立 people 和 people_visited 表，模拟内存 set，存储中间数据。
    def create_people_table(self):
        try:
            self.cursor.execute("DROP TABLE IF EXISTS people")
            self.cursor.execute("DROP TABLE IF EXISTS people_visited")
            create_people_sql = '''CREATE TABLE people(
            people_id varchar(100) NOT NULL,
            primary KEY (people_id)
            )'''
            create_people_visited_sql = '''CREATE TABLE people_visited(
            people_id varchar(100) NOT NULL,
            primary KEY (people_id)
            )'''
            self.cursor.execute(create_people_sql)
            self.cursor.execute(create_people_visited_sql)
            self.db.commit()
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
            self.db.rollback

    # 建表people_merged
    def create_people_merged_table(self):
        try:
            self.cursor.execute("DROP TABLE IF EXISTS people_merged")
            create_people_merged_sql = '''CREATE TABLE people_merged(
            people_id varchar(100) NOT NULL,
            primary KEY (people_id)
            )'''
            self.cursor.execute(create_people_merged_sql)
            self.db.commit()
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
            self.db.rollback

    # 将表 people 和 people_visited 合并为表 people_merged
    def merge_people_of_db(self):
        try:
            self.cursor.execute('''insert into people_merged select * from people
                                union select * from people_visited''')
            self.db.commit()
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
            self.db.rollback

    def create_question_table(self):
        try:
            self.cursor.execute("DROP TABLE IF EXISTS question")
            create_table_sql = '''CREATE TABLE question(
            question_id varchar(30) NOT NULL,
            url varchar(64),
            title varchar(200),
            ask_time datetime,
            followers int
            )'''
            self.cursor.execute(create_table_sql)
            self.db.commit()
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
            self.db.rollback()

    def is_people_visited(self, people_id):
        try:
            self.cursor.execute('''select COUNT(*) as cnt from people_visited
                where people_id=%s''', (people_id,))
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])

        people_count = self.cursor.fetchall()[0]['cnt']
        return 1 if (people_count == 1) else 0

    def add_to_people_db(self, people_id):
        try:
            self.cursor.execute("""insert into people(people_id)
                values (%s)""", (people_id,))
            self.db.commit()
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])

    def remove_from_people_db(self, people_id):
        try:
            self.cursor.execute("""delete from people where
                people_id=%s""", (people_id,))
            self.db.commit()
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])

    def add_to_people_visited_db(self, people_id):
        try:
            self.cursor.execute("""insert into people_visited(people_id)
                values (%s)""", (people_id,))
            self.db.commit()
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])

    def get_all_in_people_db(self):
        self.cursor.execute('''select people_id from people''')
        peoples = self.cursor.fetchall()
        ret_data = []
        if not peoples:
            return ret_data
        for one in peoples:
            ret_data.append(one['people_id'])
        return ret_data

    def get_all_in_people_merged_db(self):
        self.cursor.execute('''select people_id from people_merged''')
        peoples = self.cursor.fetchall()
        ret_data = []
        if not peoples:
            return ret_data
        for one in peoples:
            ret_data.append(one['people_id'])
        return ret_data

    def is_question_visited(self, question_id):
        try:
            self.cursor.execute('''select COUNT(*) as cnt from question
                where question_id=%s''', (question_id,))
        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        question_count = self.cursor.fetchall()[0]['cnt']
        return 1 if (question_count == 1) else 0

    # 版本 V1 方法
    def transfer_txt_to_mysql(self):
        question_db = open('question_db.txt', 'r')
        question = question_db.readline()
        question_id = question.split(' ')[0]
        question_title = question.split(' ')[1].strip() #bug 会去除标题中的空格
        while(question_id):
            try:
                self.cursor.execute("""insert into question(question_id, title)
                values (%s, %s)""", (question_id, question_title))
                self.db.commit()
            except MySQLdb.Error, e:
                print "Mysql Error %d: %s" % (e.args[0], e.args[1])
                self.db.rollback()

            question = question_db.readline()
            question_id = question.split(' ')[0]
            question_title = question.split(' ')[1].strip()
        self.db.close()

    # 版本 V1 方法
    def add_data_to_mysql(self, *para):
        try:
            self.cursor.execute('''UPDATE question
            SET ask_time=%s, followers=%s where question_id=%s
            ''', (para[0], para[1], para[2]))
            self.db.commit()

        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
            self.db.rollback()

    def add_data_to_question_db(self, *para):
        try:
            self.cursor.execute("""insert into question(question_id, title, ask_time, followers)
                values (%s, %s, %s, %s)""", (para[0], para[1], para[2], para[3]))
            self.db.commit()

        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
            self.db.rollback()

    def get_top_topic_these_days(self, look_days):
        self.cursor.execute('''select * from question where
            ask_time > DATE_SUB(%s, INTERVAL %s DAY)
            order by followers desc limit 10;
            ''', ('2015-12-13', look_days))
        top_data = self.cursor.fetchall()
        ret_data = []
        if not top_data:
            raise TypeError('Data NULL!')
        for data in top_data:
            question_url = 'https://www.zhihu.com/question/' + data['question_id']
            ret_data.append({'question_id': data['question_id'], 'ask_time': data['ask_time'],
                             'followers': data['followers'], 'title': data['title'], 'url': question_url
                             })
        return ret_data

if __name__=='__main__':
    info = DataInfo()

    # 建表
    info.create_question_table()
    info.create_people_table()
    info.create_people_merged_table()

    # 等 people 的数据抓取完成，construct_people_db_v2 函数调用之后再调用此方法
    # info.merge_people_of_db()
    info.close_mysql()