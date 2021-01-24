#!/usr/bin/python
# -*- coding: utf-8 -*-
NOTICE='''
Housekeeping the DrugStats collection

Work out the best drug name
Check category existence and redirects
Skip any with more than 2 categories

Date: 24 January 2021

Example
python pwb.py drugstats_housekeeping
'''
import urllib2
from requests import get
from BeautifulSoup import BeautifulSoup
from os import remove
import plotly
import plotly.graph_objects as go
import pywikibot, urllib2, re, sys, os
from colorama import Fore, Back, Style
from colorama import init
init()

site = pywikibot.Site('commons','commons')

maincat = pywikibot.Category(site,"Category:Charts from DrugStats")
for p in maincat.articles():
	if p.namespace()!='File:':continue
	html = p.get()
	if len(re.findall("Category:", html))>2:
		continue
	drug = html.split("''")[1].split(';')[0]
	subcat = pywikibot.Category(site, "Category:" + drug)
	exists = ''
	if subcat.exists():
		print Fore.GREEN + drug, Fore.WHITE
		#{{category redirect|Paracetamol}}
		schtml = subcat.get()
		if re.search('\{.ategory redirect', schtml):
			redir = schtml.split('ategory redirect|')[1].split('}')[0]
			subcat = pywikibot.Category(site, "Category:" + redir)
			print Fore.CYAN + "-> " + subcat.title(), Fore.WHITE
			drug = redir
	else:
		print Fore.MAGENTA + drug, Fore.WHITE
		exists = " (redlink)"
	if not re.search(re.escape("Category:" + drug), html):
		pywikibot.setAction("Add deduced [[:Category:" + drug + "]]" + exists)
		p.put(html + "\n[[Category:" + drug + "]]")
	else:
		print Fore.RED + "Already categorized", Fore.WHITE
