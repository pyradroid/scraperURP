# -*- coding:utf-8 -*-
import urllib
import urllib2
import cookielib
from PIL import Image
import pytesseract
from lxml import etree
from prettytable import PrettyTable

class URP(object):

	def __init__(self, username, passwd):
		# URP教务处登陆地址
		self.loginURL = 'http://115.24.160.162/loginAction.do'
		# 验证码图片
		self.srcImage = 'http://115.24.160.162/validateCodeAction.do?random=0.7790430092415272'
		# 登陆后的实际成绩显示页面
		self.gradeURL = 'http://115.24.160.162/gradeLnAllAction.do?type=ln&oper=qbinfo'
		self.cookies = cookielib.CookieJar()
		# 构建opener
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))
		self.data = {
			'zjh': username,
			'mm': passwd,
			'v_yzm': ''
		}
		# 所有学期各科成绩
		self.totalGrade = []
		# 各学期加权平均分
		self.Grade = []
		# 各学期绩点
		self.GPA = []

	def getValidationCode(self):
		# 获取当前session验证码图片
		picture = self.opener.open(self.srcImage).read()
		vimg = open('vimage.jpg', 'wb')
		vimg.write(picture)
		vimg.close()
		image = Image.open('.\\vimage.jpg')
		code = pytesseract.image_to_string(image).strip()
		self.data['v_yzm'] = code

	def getGradePage(self):
		error = True
		while error:
			if not self.data['v_yzm'] or error:
				self.getValidationCode()
			postedData = urllib.urlencode(self.data)
			request = urllib2.Request(self.loginURL, postedData)
			loginPage = self.opener.open(request)
			loginTree = etree.HTML(loginPage.read())
			error = loginTree.xpath('//td[@class="errorTop"]')		# 验证码错误、密码错误等错误都会出现此标志
		gradePage = self.opener.open(self.gradeURL)					# 进入成绩页面(含所有学期)
		gradeTree = etree.HTML(gradePage.read().decode('gbk'))
		gradeClasses = gradeTree.xpath('//table[@class="displayTag"]')
		return gradeClasses

	def getGrades(self):
		gradeClasses = self.getGradePage()
		for item in gradeClasses:
			courseNameList = item.xpath('.//tr[@class="odd"]/td[3]')	# 当前结点的所有符合条件的后代节点
			creditList = item.xpath('.//tr[@class="odd"]/td[5]')
			gradeList = item.xpath('.//tr[@class="odd"]/td[7]/p')
			currentGrade = []
			for kcm, xf, cj in zip(courseNameList, creditList, gradeList):
				try:
					grade = float(cj.text[:4])		# 成绩的格式为一位小数
				except UnicodeEncodeError:
					grade = cj.text.strip()			# 有些科目没给具体成绩，只给评级了
				finally:
					gotGrade = {
						'CourseName': kcm.text.strip('\r\n '),	# 去掉课程名中多余的符号
						'Credit': float(xf.text),
						'Grade': grade
					}
				currentGrade.append(gotGrade)
			self.totalGrade.append(currentGrade)

	def calculateGPA(self):
		# 计算绩点、加权平均分
		self.getGrades()
		for thisClass in self.totalGrade:
			Credits = 0
			overallGrade = 0
			overallGPA = 0
			for thisGrade in thisClass:
				credit = thisGrade['Credit']
				grade = thisGrade['Grade']
				thisGPA = 0

				if grade == u'优秀':
					grade  = 95
				if grade == u'良好':
					grade = 85
				if grade == u'中等':
					grade = 75
				if grade == u'及格':
					grade = 65

				if grade >= 90:
					thisGPA = 4
				elif grade >= 80:
					thisGPA = 3
				elif grade >=70:
					thisGPA = 2
				elif grade >= 60:
					thisGPA = 1

				Credits += credit
				overallGrade += credit * grade
				overallGPA += credit * thisGPA
			averGrade = overallGrade / Credits
			averGPA = overallGPA / Credits
			self.Grade.append(averGrade)
			self.GPA.append(averGPA)

	def printInfo(self):
		self.calculateGPA()
		classList = ['大一上','大一下','大二上','大二下','大三上','大三下','大四上','大四下']
		for className, thisClass, classGrade, classGPA in zip(classList,self.totalGrade, self.Grade, self.GPA):
			print className + ':'
			thisTable = PrettyTable(["课程名","学分","成绩"])
			thisTable.align["课程名"] = 'l'
			thisTable.padding_width = 1
			for thisGrade in thisClass:
				thisTable.add_row([thisGrade['CourseName'], thisGrade['Credit'], thisGrade['Grade']])
			print thisTable
			print '加权平均分:' + '%.2f' % classGrade + '\t\t\t\t' + '绩点:' + '%.2f' % classGPA

hebut = URP('学号', '密码')	# 在此输入学号和密码
hebut.printInfo()
