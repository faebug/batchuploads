#!/usr/bin/python
# -*- coding: utf-8 -*-
NOTICE='''
Relicense_PD-USGov.py

Housekeeping of licenses for PD-USGov main category (> 260,000 files).
https://commons.wikimedia.org/wiki/User:F%C3%A6/code/PD-USGov

Example commandline:
python pwb.py "relicense PD-USGov" -dir:~/'Google Drive/pywikibot-core/core/Faebot'

2017 February: create

Author: Fae, http://j.mp/faewm
Code license: CC-BY-SA-4.0
'''
import pywikibot, re, time, sys
from pywikibot import pagegenerators
from sys import argv
from colorama import Fore, Back, Style
from colorama import init
init()

print Fore.YELLOW + NOTICE, Fore.WHITE

site = pywikibot.getSite('commons', 'commons')
searchstrings = [
	['insource:/fema.gov|Federal Emergency Management Agency/', 'PD-USGov-FEMA'],
	['insource:/www.faa.gov|PD-USGov-FAA/','PD-USGov-FAA'],
	['insource:/PD-USGov-FSA/','PD-USGov-FSA'],
	['insource:/arm.gov|PD-USGov-ARM/','PD-USGov-ARM'],
	['insource:/= Environmental Protection Agency/', 'PD-USGov-EPA'],
	['insource:/nasa.gov/', 'PD-USGov-NASA'],
	['insource:/United States Department of Commerce|commerce.gov/i', 'PD-USGov-DOC'],
	['insource:/Food Administration/i', 'PD-USGov-FDA'],
	['insource:/www.nist.gov|PD-USGov-NIST/','PD-USGov-NIST'],
	['insource:/www.nro.gov|PD-USGov-NRO/', 'PD-USGov-NRO'],
	['insource:/Coast Guard|USCG photo/i', 'PD-USCG'],
	['insource:/Treasury Department/', 'PD-USGov-Treasury'],
	]
searchcore = 'incategory:"PD US Government" insource:/"{{PD-USGov}}"/ '

scount = 0
for searchstring in searchstrings:
	scount+=1
	print Fore.CYAN + "{:2d}".format(scount), Fore.YELLOW + "{} -> {}".format(searchstring[0], searchstring[1])
print "*"*80, Fore.WHITE

scount = 0
for searchstring in searchstrings:
	scount += 1
	print Fore.CYAN + "{}".format(scount), Fore.MAGENTA + "Searching", searchstring[0], Fore.WHITE
	pages = site.search(searchcore + searchstring[0], namespaces=6, where="text", get_redirects=False, total=None, content=False)
	count = 0
	for page in pages:
		count += 1
		print Fore.CYAN + "{}-{}".format(scount, count), Fore.GREEN + page.title()[5:-4], Fore.WHITE
		oldhtml = page.get()
		html = re.sub("\{\{PD-USGov\}\}", "{{" + searchstring[1] + "}}", oldhtml)
		escss = re.escape("{{" + searchstring[1] + "}}")
		html = re.sub(re.escape(escss +"[\n\s]*" + escss), "{{" + searchstring[1] + "}}", html)
		if len(html)!=len(oldhtml):
			comments = " ".join([r[3] for r in page.getVersionHistory()])
			if re.search("PD-USGov diffusion", comments):
				print Fore.RED + "Appears to have been previously diffused", Fore.WHITE
				continue
			action = "PD-USGov diffusion matching '{}' -> {}".format(searchstring[0], "{{" + searchstring[1] + "}}")
			pywikibot.setAction(action)
			page.put(html)
