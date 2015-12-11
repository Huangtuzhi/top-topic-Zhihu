#!/usr/bin/python
# -*- coding:utf-8 -*-

import MySQLdb
import MySQLdb.cursors


class DataInfo(object):
    def __init__(self):
        self.db = MySQLdb.connect("localhost", "root", "199194", "top_topic_zhihu",
                                  cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
        self.cursor = self.db.cursor()

    def close_mysql(self):
        self.db.close()

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
        self.db.close()

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

    def add_data_to_mysql(self, *para):
        try:
            self.cursor.execute('''UPDATE question
            SET ask_time=%s, followers=%s where question_id=%s
            ''', (para[0], para[1], para[2]))
            self.db.commit()

        except MySQLdb.Error, e:
            print "Mysql Error %d: %s" % (e.args[0], e.args[1])
            self.db.rollback()

    def get_top_topic_these_days(self):
        self.cursor.execute('''select * from question where
            ask_time > '2015-12-08 00:00:00' and ask_time < '2015-12-11'
            order by followers desc limit 10;
            ''')
        top_data = self.cursor.fetchall()
        ret_data = []
        if not top_data:
            raise TypeError('Data NULL!')
        for data in top_data:
            question_url = 'https://www.zhihu.com/question/' + data['question_id']
            ret_data.append({'question_id': data['question_id'], 'ask_time': data['ask_time'],
                             'followers': data['followers'], 'title': data['title'], 'url': question_url
                             })
            # print data['question_id'], data['title'], data['ask_time'], data['followers']
        return ret_data


if __name__=='__main__':
    info = DataInfo()

    # 新建重置 DB
    # info.create_question_table()

    # 将 txt 中数据导入到 MySQL 中
    # info.transfer_txt_to_mysql()
    # info.select()

    # 在 MySQL question 表中更新字段
    #info.add_data_to_mysql('2015-12-10', 1000, '26592438');

    # 显示最近几天 top topic
    print info.get_top_topic_these_days()