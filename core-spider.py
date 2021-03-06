# -*- coding:utf-8 -*-
"""
@author:lopt
@file:core-spider.py
@time:2019/1/414:59
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import pymysql
import datetime
import pin_sql
import get_job_id

global work_exp
work_exp = ['初中及以下','中专','中技','高中','大专','本科','硕士','博士']
global all_job_id
all_job_id = []

def get_one_page(key,page,header,date,table_name,db):
	url = 'https://search.51job.com/list/000000,000000,0000,00,9,99,' + key + ',2,' + str(page) + '.html'
	res = requests.get(url,headers = header).content.decode('gbk')
	soup = BeautifulSoup(res,'lxml')
	tags = soup.find_all("a",target="_blank",title = True,onmousedown = True,onfocus=False) #筛选出所有详细页面的链接
	page_count = soup.select('span.td')[0].text
	p = re.compile('\d+')
	page_count = int(p.findall(page_count)[0])
	for h in tags:
		if "https://jobs.51job.com"in h['href']:
			job_id = h['href'][h['href'].rfind("/") + 1:h['href'].rfind(".")]
			if int(job_id) not in all_job_id :
				job_dic = get_detail_page(h['href'],date)
				operate_and_save(job_dic,table_name,db)
				time.sleep(0.1)
			else:
				print("----发现重复job_id----")
				continue
		else:
			continue
	return page_count


def get_detail_page(href,date):
	global all_job_id
	print(href)
	try:
		res = requests.get(href).text
	except Exception as e:
		print(e)
	job_dic = {}
	soup = BeautifulSoup(res,"lxml")
	job_dic['job_id'] = href[href.rfind('/')+1:href.rfind('.')]
	all_job_id.append(int(job_dic['job_id']))
	job_dic['job_name'] = soup.select("div.cn  h1")[0].text.strip().replace('\t','')
	results = job_classify(job_dic['job_name'])
	job_dic['job_function'] = results['function']
	job_dic['job_rank'] = results['rank']
	job_dic['salary'] = soup.select("div.cn  strong")[0].text.strip()
	job_dic['salary_down'] = get_salary(job_dic['salary'])['salary_down']
	job_dic['salary_up'] = get_salary(job_dic['salary'])['salary_up']
	job_dic['company_name'] = soup.select("div.cn  p a")[0].text.strip()
	temp_text = soup.select("div.cn  p.msg")[0].text.strip().split("  |  ")  #得到的值是用|分割的字符串，所以转换成list方便操作
	if temp_text[0].find('-') == -1: #城市有两种  “市-区”、“市” 通过切字符串确定到市
		job_dic['city'] = temp_text[0].strip()
	else:
		job_dic['city'] = temp_text[0][:(temp_text[0].find('-'))].strip()

	temp_text_for = temp_text[1:] #地区一定存在，所以截取掉0，循环中需要i+1取值
	for i in range(len(temp_text_for)):
		if "经验" in temp_text_for[i]:
			job_dic['work_exp'] = temp_text_for[i].strip()
		elif temp_text_for[i] in work_exp:
			job_dic['edu_level'] = temp_text_for[i].strip()
		elif '招' in temp_text_for[i]:
			job_dic['recruit_count'] = temp_text_for[i].strip()
		elif '发布' in temp_text_for[i]:
			job_dic['update_date'] = temp_text_for[i].strip()

	job_dic['job_type'] = soup.select("div.tCompany_main  div.bmsg a.el")[0].text.strip()
	job_dic['company_type'] = soup.select("p.at",limit = 1)[0].text
	job_dic['company_size'] = soup.select("div.com_tag p",limit = 2)[1].text

	jd_temp = soup.select("div.tCompany_main  div.bmsg")[0].text.strip()
	job_dic['job_describe'] = ''.join(jd_temp[:jd_temp.find('职能类别')].split())
	'''通过定位所有的tag进行循环操作获得数据
	industry = []
	for i in soup.select("div.com_tag p a"):
		industry.append(i.text)
	job_dic['industry'] = ''.join(industry)
	'''
	'''通过定位span后寻找其父亲节点然后取其中的属性'''
	job_dic['company_industry'] = soup.select('span.i_trade')[0].find_parent()['title']
	job_dic['welfare'] = soup.select('div.t1')[0].text.strip().replace('\n',',').replace('\t','')
	#从jd中获取关键字，并存贮到对应的字段中
	key_result = key_word_classify(job_dic['job_describe'])
	job_dic['kw_data'] = key_result['数据'] #数据
	job_dic['kw_innovation'] = key_result['创新'] #创新
	job_dic['kw_communication'] = key_result['沟通']#沟通
	job_dic['kw_coordination'] = key_result['协调']#协调
	job_dic['kw_labor_law'] = key_result['劳动法']
	job_dic['kw_logic'] = key_result['逻辑']
	job_dic['kw_responsibility'] = key_result['责任']
	job_dic['kw_team'] = key_result['团队']
	job_dic['kw_resist_compression'] = key_result['抗压']
	job_dic['kw_learning'] = key_result['学习']
	job_dic['kw_analysis'] = key_result['分析']
	job_dic['kw_optimization'] = key_result['优化']
	job_dic['got_day'] = date #str(date.strftime("%Y-%m-%d"))
	return  job_dic


def get_salary(salary):
	'''用于解析工资,并分解出工资区间'''
	job_salary = {'salary_down':0,'salary_up':0}
	if salary:
		if '天' in salary:
			job_salary['salary_down'] = 22*int(salary[:-3])
			job_salary['salary_up'] = 22*int(salary[:-3])
		elif '月' in salary:
			if '千' in salary:
				if "以下" in salary:
					job_salary['salary_down'] = float(salary[:-5]) * 1000
					job_salary['salary_up'] = float(salary[:-5]) * 1000
				else:
					job_salary['salary_down'] = float(salary[:salary.find('-')]) * 1000
					job_salary['salary_up'] = float(salary[salary.find('-') + 1:-3]) * 1000
			elif '万' in salary:
				if "以上" in salary:
					job_salary['salary_down'] = float(salary[:-5]) * 10000
					job_salary['salary_up'] = float(salary[:-5]) * 10000
				else:
					job_salary['salary_down'] = float(salary[:salary.find('-')]) * 10000
					job_salary['salary_up'] = float(salary[salary.find('-') + 1:-3]) * 10000
			else:
				print("----按月工资工资格式出现异常")
		elif '年' in salary:
			if "以上" in salary:
				job_salary['salary_down'] = round(float(salary[:-5]) * 10000 / 12,1)
				job_salary['salary_up'] = round(float(salary[:-5]) * 10000 / 12,1)
			elif "以下" in salary:
				job_salary['salary_down'] = round(float(salary[:-5]) * 10000 / 12,1)
				job_salary['salary_up'] = round(float(salary[:-5]) * 10000 / 12,1)
			else:
				job_salary['salary_down'] = round(float(salary[:salary.find('-')]) * 10000 / 12,1)
				job_salary['salary_up'] = round(float(salary[salary.find('-') + 1:-3]) * 10000 / 12,1)

		else:
			print('----工资格式出现异常----')

	else:
		print("----工资为空----")
	return job_salary


def job_classify(job_name):
	"""对工作名称进行职能职级分类"""
	job_class = {'function':'','rank':''}
	functions = ['HRBP','人力','人事','招聘','培训','绩效','关系','组织发展','薪酬','猎头','人资']
	ranks = ['实习生','专员','总监','主管','经理']
	for fn in functions:
		if fn in job_name.upper():
			job_class['function'] = fn
			break
		elif '组织' in job_name or '发展' in job_name:
			job_class['function'] = '组织发展'
			break
		else:
			job_class['function'] = '未识别'

	for rk in ranks:
		if '助理'in job_name:
			job_class['rank'] = '专员'
		elif rk in job_name:
			job_class['rank'] = rk
		elif '管培'in job_name or '员'in job_name:
			job_class['rank'] = '专员'
		elif '主任'in job_name:
			job_class['rank'] = '经理'
		elif '负责人' in job_name:
			job_class['rank'] = '总监'
	return job_class


def key_word_classify(job_describe):
	"""对岗位描述与岗位职责进行关键词提取"""
	key_word = ['数据','创新','沟通','协调','劳动法','逻辑','责任','团队','抗压','学习','分析','优化']
	result = {'数据':3,'创新':3,'沟通':3,'协调':3,'劳动法':3,'逻辑':3,'责任':3,'团队':3,'抗压':3,'学习':3,'分析':3,'优化':3}
	for k in range(len(key_word)):
		if key_word[k] in job_describe:
			result[key_word[k]] = 1
		else:
			result[key_word[k]] = 0
	return result


def operate_and_save(job_dic,table_name,db):
	print(job_dic)
	sql = pin_sql.get_i_sql(table_name,job_dic)
	try:
		cursor = db.cursor()
		cursor.execute(sql)
		db.commit()
	except Exception as e:
		db.rollback()
		print("----operate_and_save----发生错误")
		print(e)


def pre_data(date):
	table_name = "tb_51job_" + str(date)
	try:
		db = pymysql.connect(
			host = 'localhost',
			port = 3306,
			user = 'root',
			password = 'root'
		)
	except Exception as e:
		print("----pre_data数据库连接出错----")
		print(e)
	try:
		cursor = db.cursor()
		sql = """CREATE DATABASE IF NOT EXISTS hr_analysis DEFAULT CHARACTER SET utf8 """
		cursor.execute(sql)
		sql = """USE hr_analysis"""
		cursor.execute(sql)
		sql = """CREATE TABLE IF NOT EXISTS {0}(
			job_id INT(20) NOT NULL UNIQUE,
			city VARCHAR(254),
			job_name VARCHAR(254),
			salary VARCHAR(254),
			salary_down DECIMAL (20,2),
			salary_up DECIMAL (20,2),
			company_name VARCHAR(254),
			company_size VARCHAR(254),
			company_type VARCHAR(254),
			company_industry VARCHAR(254),
			work_exp VARCHAR(254),
			edu_level VARCHAR(254),
			recruit_count  VARCHAR(254),
			job_function VARCHAR (254),
			job_rank VARCHAR (254),
			job_type VARCHAR(254),
			welfare VARCHAR(254),
			update_date VARCHAR(254),
			job_describe VARCHAR(4000) ,
			got_day DATE ,
			kw_data INT(10),kw_innovation INT(10),kw_communication INT(10),kw_coordination INT(10),
 			kw_labor_law INT(10),kw_logic INT(10),kw_responsibility INT(10),kw_team INT(10),
 			kw_resist_compression INT(10),kw_learning INT(10),kw_analysis INT(10),kw_optimization INT(10)
			);""".format(table_name)
		cursor.execute(sql)
		db.commit()
	except Exception as e:
		print("----创建数据库出错----")
		print(e)
	return table_name,db



def main(key_word,page):
	global all_job_id
	date = datetime.date.today().strftime("%Y%m%d")
	f_date = datetime.date.today().strftime("%Y-%m-%d")
	table_name,db = pre_data(date)
	all_job_id = get_job_id.get_job_id(table_name)
	header = {
		'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
		'Connection':'close'
	}
	while True:
		page_count = get_one_page(key_word,page,header,f_date,table_name,db)
		if page < page_count:
			page += 1
		else:
			db.close()
			break


if __name__ == '__main__':
	main('人力资源',1)
	#get_detail_page("https://jobs.51job.com/shanghai/109669333.html?s=01&t=0")