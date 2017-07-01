#!/usr/bin/python
# -*- coding: utf-8 -*-
NOTICE = '''
jpg_tiff_matching.py
Go through a category checking for jpg tiff pairs.
Two way sync visible cats.
Report on-wiki.

Example calls:
nice -n 19 python pwb.py jpg_tiff_matching -dir:Faebot

Date: 1 July 2017
Author: Fae, http://j.mp/faewm
Permissions: CC-BY-SA-4.0
'''

import pywikibot, sys, re, string, time
from sys import argv
from time import sleep
from colorama import Fore, Back, Style
from colorama import init
init()

site = pywikibot.getSite('commons', 'commons')

print Fore.GREEN + NOTICE, Fore.WHITE

catname = u"Category:Images from the Canadian Copyright Collection at the British Library"
category = pywikibot.Category(site, catname)
pairs = []
count = 0
for image in category.members():
	if image.namespace() != ":File:":
		continue
	if not re.search("\(HS85-10-\d+\).jpg", image.title()):
		continue
	pair = []
	for ext in ['tif', 'tiff']:
		tiff = re.sub("\.jpg$", " original." + ext, image.title())
		tim = pywikibot.ImagePage(site, tiff)
		if tim.exists():
			pair = [image, tim]
			break
	if pair == []:
		continue
	count += 1
	html = ""; ccount = 0
	changesdone = False
	for cat in image.categories():
		if cat.isHiddenCategory():
			continue
		if cat not in tim.categories():
			ccount += 1
			html += "\n[[" + cat.title() + "]]"
	if html != "":
		pywikibot.setAction("Add {} categories from jpeg".format(ccount))
		changesdone = True
		ploop = True
		while ploop:
			try:
				tim.put(tim.get() + html)
				ploop = False
			except Exception as e:
				print Fore.RED + str(e), Fore.WHITE
				sleep(10)
	html = ""; ccount = 0
	for cat in tim.categories():
		if cat.isHiddenCategory():
			continue
		if cat not in image.categories():
			ccount += 1
			html += "\n[[" + cat.title() + "]]"
	if html != "":
		pywikibot.setAction("Add {} categories from TIFF".format(ccount))
		changesdone = True
		ploop = True
		while ploop:
			try:
				image.put(image.get() + html)
				ploop = False
			except Exception as e:
				print Fore.RED + str(e), Fore.WHITE
				sleep(10)
	if changesdone:
		pairs.append(pair)
		if count % 25 == 0:
			print Fore.CYAN, count, Fore.GREEN + pair[0].title()[5:-4], Fore.WHITE
results = "\n{|class='wikitable'\n!JPEG!!TIFF\n"
for p in pairs:
	results += "|-\n|[[:{}|{}]]||[[:{}|TIFF]]".format(p[0].title(), 'HS85' + p[0].title().split('(HS85')[1].split(')')[0], p[1].title())
results += "\n|}"

log = pywikibot.Page(site, 'User:Faebot/SandboxB')
pywikibot.setAction("Add results of BL cat sync run")
ploop = True
while ploop:
	try:
		log.put(log.get() + results)
		ploop = False
	except Exception as e:
		print Fore.RED + str(e), Fore.WHITE
		sleep(10)
