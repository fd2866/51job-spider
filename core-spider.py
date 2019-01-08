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

global work_exp
work_exp = ['初中及以下','中专','中技','高中','大专','本科','硕士','博士']


def get_one_page(key,page,header):

	url = 'https://search.51job.com/list/000000,000000,0000,00,9,99,' + key + ',2,' + str(page) + '.html'
	res = requests.get(url,headers = header).content.decode('gbk')
	soup = BeautifulSoup(res,'lxml')
	tags = soup.find_all("a",target="_blank",title = True,onmousedown = True,onfocus=False) #筛选出所有详细页面的链接
	page_count = soup.select('span.td')[0].text
	p = re.compile('\d+')
	page_count = int(p.findall(page_count)[0])
	for h in tags:
		if "https://jobs.51job.com"in h['href']:
			get_detail_page(h['href'])
			time.sleep(0.1)
		else:
			continue
	return page_count


def get_detail_page(href):
	print(href)
	try:
		res = requests.get(href).text
	except Exception as e:
		print(e)
	job_dic = {}
	soup = BeautifulSoup(res,"lxml")
	job_dic['job_name'] = soup.select("div.cn  h1")[0].text.strip().replace('\t','')
	job_dic['salary'] = soup.select("div.cn  strong")[0].text.strip()
	'''
	if '天' in job_dic['salary']:
		job_dic['salary_down'] = 22*int(job_dic['salary'][:-3])
		job_dic['salary_down'] = 22*int(job_dic['salary'][:-3])
	elif '月' in job_dic['salary']:
		job_dic
			'''
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
			job_dic['update_day'] = temp_text_for[i].strip()
	#job_dic['work_exp'] = temp_text[1].strip()
	#job_dic['edu_level'] = temp_text[2].strip()
	#job_dic['recruit_count'] = temp_text[3].strip()
	#job_dic['update_day'] = temp_text[4].strip()
	jd_temp = soup.select("div.tCompany_main  div.bmsg")[0].text.strip()
	job_dic['job_describe'] = ''.join(jd_temp[:jd_temp.find('职能类别')].split())
	key_result = key_word_classify(job_dic['job_describe'])
	job_dic['data'] = key_result['数据'] #数据
	job_dic['innovation'] = key_result['创新'] #创新
	job_dic['communication'] = key_result['沟通']#沟通
	job_dic['coordination'] = key_result['协调']#协调
	job_dic['labor_law'] = key_result['劳动法']
	job_dic['logic'] = key_result['逻辑']
	job_dic['responsibility'] = key_result['责任']
	job_dic['team'] = key_result['团队']
	job_dic['resist_compression'] = key_result['抗压']
	job_dic['learning'] = key_result['学习']
	job_dic['analysis'] = key_result['分析']
	job_dic['optimize'] = key_result['优化']
	job_dic['job_type'] = soup.select("div.tCompany_main  div.bmsg a.el")[0].text.strip()
	job_dic['company_type'] = soup.select("p.at",limit = 1)[0].text
	job_dic['company_size'] = soup.select("div.com_tag p",limit = 2)[1].text
	'''通过定位所有的tag进行循环操作获得数据
	industry = []
	for i in soup.select("div.com_tag p a"):
		industry.append(i.text)
	job_dic['industry'] = ''.join(industry)
	'''
	'''通过定位span后寻找其父亲节点然后取其中的属性'''
	job_dic['industry'] = soup.select('span.i_trade')[0].find_parent()['title']
	job_dic['welfare'] = soup.select('div.t1')[0].text.strip().replace('\n',',').replace('\t','')
	print(job_dic)


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


def pre_data():
	try:
		db = pymysql.connect(
			host = 'localhost',
			port = 3306,
			user = 'root',
			password = 'Zhangyang5'
		)
	except Exception as e:
		print("----数据库连接出错----")
		print(e)
	try:
		cursor = db.cursor()
		sql = """CREATE DATABASE IF NOT EXISTS hr_analysis DEFAULT CHARACTER SET utf8 """
		cursor.execute(sql)
		sql = """USE hr_analysis"""
		cursor.execute(sql)

	except Exception as e:
		print("----创建数据库出错----")
		print(e)



def main(key_word,page):
	header = {
		'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
		'Connection':'close'
	}
	while True:
		page_count = get_one_page(key_word,page,header)
		if page < page_count:
			page += 1
		else:
			break


if __name__ == '__main__':
	main('人力资源',1)
	#get_detail_page("https://jobs.51job.com/shanghai/109669333.html?s=01&t=0")