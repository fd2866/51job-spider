# -*- coding:utf-8 -*-
"""
@author:lopt
@file:pin_sql.py
@time:2019/1/1111:20
"""

# encoding=utf-8
import pymysql

def safe(s):
    return pymysql.escape_string(s)


def get_i_sql(table, dict):
    '''
    生成insert的sql语句
    @table，插入记录的表名
    @dict,插入的数据，字典
    '''
    sql = 'insert into %s set ' % table
    sql += dict_2_str(dict)
    return sql


def get_s_sql(table, keys, conditions, isdistinct=0):
    '''
        生成select的sql语句
    @table，查询记录的表名
    @key，需要查询的字段
    @conditions,插入的数据，字典
    @isdistinct,查询的数据是否不重复
    '''
    if isdistinct:
        sql = 'select distinct %s ' % ",".join(keys)
    else:
        sql = 'select  %s ' % ",".join(keys)
    sql += ' from %s ' % table
    if conditions:
        sql += ' where %s ' % dict_2_str_and(conditions)
    return sql


def get_u_sql(table, value, conditions):
    '''
        生成update的sql语句
    @table，查询记录的表名
    @value，dict,需要更新的字段
    @conditions,插入的数据，字典
    '''
    sql = 'update %s set ' % table
    sql += dict_2_str(value)
    if conditions:
        sql += ' where %s ' % dict_2_str_and(conditions)
    return sql


def get_d_sql(table, conditions):
    '''
        生成detele的sql语句
    @table，查询记录的表名

    @conditions,插入的数据，字典
    '''
    sql = 'delete from  %s  ' % table
    if conditions:
        sql += ' where %s ' % dict_2_str_and(conditions)
    return sql


def dict_2_str(dictin):
    '''
    将字典变成，key='value',key='value' 的形式
    '''
    tmplist = []
    for k, v in dictin.items():
        tmp = "%s='%s'" % (str(k), safe(str(v)))
        tmplist.append(' ' + tmp + ' ')
    return ','.join(tmplist)


def dict_2_str_and(dictin):
    '''
    将字典变成，key='value' and key='value'的形式
    '''
    tmplist = []
    for k, v in dictin.items():
        tmp = "%s='%s'" % (str(k), safe(str(v)))
        tmplist.append(' ' + tmp + ' ')
    return ' and '.join(tmplist)

if __name__ == "__main__":
	dic={'job_id': '70260283', 'job_name': '人力资源部实习生', 'salary': '', 'salary_down': None, 'salary_up': None, 'company_name': '上海宝山宜家家居有限公司', 'city': '上海', 'work_exp': '无工作经验', 'recruit_count': '招若干人', 'update_date': '01-11发布', 'job_type': '人事助理', 'company_type': '外资（欧美）', 'company_size': '150-500人', 'job_describe': '1.对人力资源工作感兴趣2.做事细心负责3.乐于沟通4.周一至周五至少能提供3天工作时间5.英语读写良好', 'company_industry': '批发/零售,家具/家电/玩具/礼品', 'welfare': '', 'kw_data': 0, 'kw_innovation': 0, 'kw_communication': 1, 'kw_coordination': 0, 'kw_labor_law': 0, 'kw_logic': 0, 'kw_responsibility': 0, 'kw_team': 0, 'kw_resist_compression': 0, 'kw_learning': 0, 'kw_analysis': 0, 'kw_optimization': 0, 'got_day': '2019-01-11'}
	sql= get_i_sql("tb_51job_20190111",dic)
	print(sql)

