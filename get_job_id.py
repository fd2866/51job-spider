# -*- coding:utf-8 -*-
"""
@author:lopt
@file:get_job_id.py
@time:2019/1/1414:22
"""
import pymysql


def get_job_id(table_name):
	all_job_id = []
	db = pymysql.connect(
		host = 'localhost',
		port = 3306,
		user = 'root',
		password = 'root',
		db = 'hr_analysis',
	)

	sql = "SELECT job_id FROM %s"%table_name

	try:
		cursor = db.cursor()
		cursor.execute(sql)
		all_id = cursor.fetchall()
		for id in all_id:
			all_job_id.append(id[0])
	except Exception as e:
		print("---get_job_id----数据库查询出现错误")
		print(e)
	db.close()
	return all_job_id