#!/usr/bin/python
# -*- coding: utf-8 -*-
NOTICE='''
Upload from ClinCalc DrugStats Database

First pass used the 300 drugs list.
Second pass hacked the list by exhaustive 3-letter searches.

Date: 23 January 2021

Example
python pwb.py upload_drugstats
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

def up(source, pagetitle, desc, comment, iw):
	if source[:4] == 'http':
		source_url=source; source_filename=None
		# Resolve url redirects to find end target (the API will not do this)
		headers = { 'User-Agent' : 'Mozilla/5.0' }
		req = urllib2.Request(source_url, None, headers)
		res = urllib2.urlopen(req)
		source_url = res.geturl()
	else:
		source_url=None; source_filename=source

	if iw:
		site.upload(pywikibot.FilePage(site, 'File:' + pagetitle),
			source_filename=source_filename,
			source_url=source_url,
			comment=comment,
			text=desc,
			ignore_warnings = True,
			chunk_size= 400000,#1048576,
			#async = True,
			)
	else:
		site.upload(pywikibot.FilePage(site, 'File:' + pagetitle),
			source_filename=source_filename,
			source_url=source_url,
			comment=comment,
			text=desc,
			ignore_warnings = False,
			chunk_size = 400000,#1048576,
			#async = True,
			)

def drugchart(durl):
	dhtml = urllib2.urlopen(durl).read()
	dsoup = BeautifulSoup(dhtml)
	dtitle = dsoup.find('h1', {'class':'HeadingText'}).text.strip()
	#print dtitle
	cotdata = dsoup.find('div', id='divCostOverTime').findNext('script').text
	potdata = dsoup.find('div', id='divPrescriptionsOverTime').findNext('script').text
	cotdata = eval(cotdata.split('data.addRows(')[1].split(')')[0])
	potdata = eval(potdata.split('data.addRows(')[1].split(')')[0])
	yearc = [i[0] for i in cotdata]
	yearp = [i[0] for i in potdata]
	if len(yearc)<2 or len(yearp)<2:
		return False, '', cotdata, potdata, '', ''
	ymax, ymin = max(yearc), min(yearc)
	totcost = [i[1] for i in cotdata]
	oopcost = [i[2] for i in cotdata]
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=yearc, y=totcost, name="Total Cost"))
	fig.add_trace(go.Scatter(x=yearc, y=oopcost, name="Out of Pocket Cost"))
	fig.update_layout(title=dtitle + " drug cost over time ({}-{})".format(ymin,ymax),
			xaxis_title = "Year",
			yaxis_title="Price USD",
			margin=dict(pad=0))
	fig.update_yaxes(rangemode="tozero")
	fig.update_xaxes(tickmode='array', tickvals=yearc, automargin=False)
	ymax, ymin = max(yearp), min(yearp)
	pres = [i[1] for i in potdata]
	figp = go.Figure()
	figp.add_trace(go.Scatter(x=yearp, y=pres, name="Prescriptions"))
	figp.update_layout(title=dtitle + " number of prescriptions ({}-{})".format(ymin,ymax),
			xaxis_title = "Year",
			yaxis_title="Prescriptions, USA",
			margin=dict(pad=0))
	figp.update_yaxes(rangemode="tozero")
	figp.update_xaxes(tickmode='array', tickvals=yearp, automargin=False)
	return fig, figp, dtitle, cotdata, potdata, dsoup

defaulttext = u"""{{Current}}
{{Mbox
|text= Data from DrugStats is expected to be updated annually in August. 
|type= message
}}
== {{int:filedesc}} ==
{{information
"""

def upthisdrug(drug):
	global count
	source = 'https://clincalc.com/DrugStats/' + drug['href']
	dname = drug['href'].split('/')[-1]
	fig, figp, title, cotdata, potdata, soup = drugchart(source)
	if not fig:
		print Fore.MAGENTA, count, drug, "not enough data", Fore.WHITE
		return False
	desc = soup.find('meta', {'name':'description'})['content']
	keywords = soup.find('meta', {'name':'description'})['content'].split(' including:')[-1].strip()
	date = soup.find('span', id='lblLastUpdated').text
	for c in [[ "prescriptions", figp, potdata ],
			  [ "costs", fig, cotdata ]]:
		filename = dname + " {} (DrugStats).svg".format(c[0])
		page=pywikibot.Page(site, u'File:'+filename)
		if page.exists() and re.search(re.escape(date), page.get()):
			print Fore.MAGENTA, count, "exists", Fore.WHITE
			return False
		print Fore.CYAN, count, Fore.GREEN + filename, Fore.WHITE
		dd = defaulttext
		dd += "|description = {{en|1=" + c[0].title() + " chart for ''" + title + "''."
		dd += "\nKeywords: " + keywords
		dd += "\n<br>Chart data: \n<pre style='color:darkgreen;font-family:monospace;margin-left:1em;border:1px darkgreen solid;'>\n " + re.sub('[\[\]]', '', re.sub('],',',\n',str(c[2]))) + "</pre>\n }}"
		dd += "\n|source = " + source
		dd += "\n|author = ClinCalc DrugStats" 
		dd += "\n|date = " + date
		dd += "\n|permission = Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
		dd += "}}\n=={{int:license-header}}==\n"
		dd += "{{Cc-by-sa-4.0|1=[https://clincalc.com/DrugStats/ ClinCalc DrugStats]}}\n\n"
		dd += u"[[Category:Charts from DrugStats]]\n[[Category:Images uploaded by Fæ]]"
		#print Fore.YELLOW + dd, Fore.WHITE
		#c[1].show()
		home = os.path.expanduser("~")
		local = home + "/Downloads/TEMP/"+filename
		c[1].write_image(local, format="svg", width=1024, height = 768)
		comment = "[[User_talk:Fæ/DrugStats|DrugStats]] chart for {} {}".format(title, date)
		pywikibot.setAction(comment)
		if len(sys.argv)<2:
			up(local, filename, dd, comment, True)
		remove(local)
		return True

topurl = "https://clincalc.com/DrugStats/Top300Drugs.aspx"
html = urllib2.urlopen(topurl).read()
soup = BeautifulSoup(html)
drugs = soup.findAll('a', href=re.compile('Drugs/.*'))
print Fore.GREEN + NOTICE
print '*'*80
print Fore.CYAN, soup.find('meta', {'name':'description'})['content']
print Fore.CYAN, "Drugs found", len(drugs), Fore.WHITE
count = 0
'''for drug in drugs:
	count += 1
	upthisdrug(drug)'''

chars="abcdefghijklmnopqrstuvwxyz";charx=[];charxx=[]
for i in range(0, len(chars)):
	charx.append(chars[i])
for a in charx:
	for b in charx:
		for c in charx:
			charxx.append(a+b+c)
print len(charxx)
alldrugs=set()
for x in charxx:
	url = "https://clincalc.com/DrugStats/Default.aspx?query=drugName&d=" + x
	html = urllib2.urlopen(url).read()
	soup = BeautifulSoup(html)
	durls = soup.findAll('a')
	if len(durls)==0: continue
	foundsome = False
	print Fore.CYAN, x,
	for d in durls:
		href = d['href'].split('/')[1]
		if href not in alldrugs:
			if not foundsome: print
			foundsome = True
			print Fore.GREEN,href,
			alldrugs.add(href)
			outcome = upthisdrug('Drugs/' + href)
	if foundsome:
		print
		print Fore.YELLOW, len(alldrugs), Fore.WHITE
