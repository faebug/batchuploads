#!/usr/bin/python
# -*- coding: utf-8 -*-
NOTICE='''
Relicense_PD-USGov.py

Housekeeping of licenses for PD-USGov main category (> 260,000 files).
https://commons.wikimedia.org/wiki/User:F%C3%A6/code/PD-USGov

Example commandline:
python pwb.py "relicense PD-USGov" -dir:Faebot

2017 February: create
2017 March: Integrated suggested filters, added optional categorization

Author: Fae, http://j.mp/faewm
Code license: CC-BY-SA-4.0
'''
import pywikibot, re, time, sys
from pywikibot import pagegenerators
from sys import argv
argv.pop()

from colorama import Fore, Back, Style
from colorama import init
init()

print Fore.YELLOW + NOTICE, Fore.WHITE

site = pywikibot.getSite('commons', 'commons')
searchstrings = [
	['insource:/MUTCD/', 'PD-USGov-MUTCD'],
	['insource:/fema.gov|Federal Emergency Management Agency/', 'PD-USGov-FEMA'],
	['insource:/senate.gov|PD-USGov-Congress/','PD-USGov-Congress'],
	['insource:/dhs.gov|PD-USGov-DHS/','PD-USGov-DHS'],
	['insource:/energy.gov|doe.gov|PD-USGov-DOE/', 'PD-USGov-DOE'],
	['insource:/Fish and Wildlife|fws.gov|PD-USGov-FWS/', 'PD-USGov-FWS'],
	['insource:/www.faa.gov|PD-USGov-FAA/','PD-USGov-FAA'],
	['insource:/PD-USGov-FSA/','PD-USGov-FSA'],
	['insource:/PD-USGov-Award/','PD-USGov-Award'],
	['insource:/ntsb.gov|PD-USGov-NTSB/','PD-USGov-NTSB'],
	['insource:/arm.gov|PD-USGov-ARM/','PD-USGov-ARM'],
	['insource:/= Environmental Protection Agency/', 'PD-USGov-EPA'],
	['insource:/nasa.gov/', 'PD-USGov-NASA'],
	['uscourts.gov', 'PD-USGov-Judiciary'],
	['insource:/United States Department of Commerce|commerce.gov/i', 'PD-USGov-DOC'],
	['insource:/Food Administration/i', 'PD-USGov-FDA'],
	['insource:/www.nist.gov|PD-USGov-NIST/','PD-USGov-NIST'],
	['insource:/www.nro.gov|PD-USGov-NRO/', 'PD-USGov-NRO'],
	['insource:/Coast Guard|USCG photo/i', 'PD-USCG'],
	['insource:/samhsa.gov|Mental Health Services Administration/i', 'PD-USGov-HHS'],
	['insource:/cdc.gov|United States Department of Health|Centers? for Disease Control/i', 'PD-USGov-HHS-CDC'],
	['insource:/Treasury Department|Office for Emergency Management/', 'PD-USGov-Treasury'],
	['insource:/af.mil/', 'PD-USAF'],
	['insource:/navy.mil/', 'PD-USGov-Military-Navy'],
	['insource:/marines.mil/', 'PD-USMC'],
	['insource:/army.mil/', 'PD-USArmy'],
	['insource:/39736050@N02/', 'PD-USGov-FDA', 'Images from the United States Food and Drug Administration'],
	['insource:/75182224@N04/', 'PD-USGov-NPS', 'Files from the National Park Service Alaska Region Flickr stream'],
	['insource:/72578886@N08/', 'PD-USGov-NPS', 'Files from Arches NPS Flickr stream'],
	['insource:/78206310@N03/', 'PD-USGov-NPS', 'Files from Canyonlands NPS Flickr stream'],
	['insource:/77660923@N08/', 'PD-USGov-NPS', 'Files from Congaree NPS Flickr stream'],
	['insource:/57557144@N06/', 'PD-USGov-NPS', 'Files from DenaliNPS Flickr stream'],
	['insource:/56295925@N07/', 'PD-USGov-NPS', 'Files from Everglades NPS Flickr stream'],
	['insource:/43288043@N04/', 'PD-USGov-NPS', 'Files from Glacier National Park Service Flickr stream'],
	['insource:/50693818@N08/', 'PD-USGov-NPS', 'Files from Great Sand Dunes NPS Flickr stream'],
	['insource:/115357548@N08/', 'PD-USGov-NPS', 'Files from Joshua Tree National Park Flickr stream'],
	['insource:/99350217@N03/', 'PD-USGov-NPS', 'Files from Katmai NPS Flickr stream'],
	['insource:/61860846@N05/', 'PD-USGov-NPS', 'Files from Lassen Volcanic NPS Flickr stream'],
	['insource:/78037339@N03/', 'PD-USGov-NPS', 'Files from Mount Rainier NPS Flickr stream'],
	['insource:/127033241@N04/', 'PD-USGov-NPS', 'Files from RockyNPS Flickr stream'],
	['insource:/64710613@N03/', 'PD-USGov-NPS', 'Files from Saguaro NPS Flickr stream'],
	['insource:/67015038@N06/', 'PD-USGov-NPS', 'Files from Shenandoah NPS Flickr stream'],
	['insource:/80223459@N05/', 'PD-USGov-NPS', 'Files from Yellowstone NPS Flickr stream'],
	['insource:/54168808@N03/', 'PD-USGov-NPS', 'Files from Zion NPS Flickr stream'],
	['insource:/46658241@N06/', 'PD-USGov-USAID', 'USAID IMAGES'],
	['insource:/41937383@N07/', 'PD-USGov-Military-Army-USACE', 'Files from U.S. Army Corps of Engineers Detroit District Flickr stream'],
	['insource:/40704398@N05/', 'PD-USGov-Military-Army-USACE', 'Files from New York District, U.S. Army Corps of Engineers Flickr stream'],
	['insource:/52057813@N07/', 'PD-USGov-Military-Army-USACE', 'Files from U.S. Army Corps of Engineers Sacramento District Flickr stream'],
	['insource:/91981596@N06/', 'PD-USGov-BLM', 'Photographs by Bureau of Land Management'],
	['insource:/50169152@N06/', 'PD-USGov-BLM', 'Files from the Bureau of Land Management Oregon and Washington Flickr stream'],
	['insource:/55893585@N08/', 'PD-USGov-BLM', 'Photographs by the Nevada Bureau of Land Management'],
	['insource:/54593278@N03/', 'PD-USGov-DHS', 'Files from the U.S. Customs and Border Protection Flickr stream'],
	['insource:/39955793@N07/', 'PD-USGov-Military', 'Files from the U.S. Department of Defense Flickr stream'],
	['insource:/42310076@N04/', 'PD-USGov-Military', 'Files from the Chairman of the Joint Chiefs of Staff Flickr stream'],
	['insource:/78595004@N08/', 'PD-USGov-Military', 'Files from the U.S. OSD Deputy Secretary of Defense Flickr stream'],
	['insource:/68842444@N03/', 'PD-USGov-Military', 'Files from the U.S. Secretary of Defense Flickr stream'],
	['insource:/48445211@N06/', 'PD-USGov-ED', 'Files from the U.S. Department of Education Flickr stream'],
	['insource:/37916456@N02/', 'PD-USGov-DOE', 'Files from ENERGY.GOV Flickr stream'],
	['insource:/126057486@N04/', 'PD-USGov-DHS', 'Files from the U.S. Department of Homeland Security Flickr stream'],
	['insource:/9364837@N06/', 'PD-USGov-DOS', 'Files from the U.S. Department of State Flickr stream'],
	['insource:/47923257@N08/', 'PD-USGov-Treasury', 'Files from U.S. Department of the Treasury Flickr stream'],
	['insource:/130809712@N08/', 'PD-USGov-FBI', 'Files from the Federal Bureau of Investigation Flickr stream'],
	['insource:/50838842@N06/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Headquarters Flickr stream'],
	['insource:/49208525@N08/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Midwest Region Flickr stream'],
	['insource:/51986662@N05/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Mountain-Prairie Region Flickr stream'],
	['insource:/52133016@N08/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Pacific Region Flickr stream'],
	['insource:/54430347@N04/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Pacific Southwest Region Flickr stream'],
	['insource:/46536834@N08/', 'PD-USGov-FWS', 'Files from the US Fish and Wildlife Service - Recovery Act Team Flickr stream'],
	['insource:/54430347@N04/', 'PD-USGov-FWS', 'U.S. Fish and Wildlife Service Pacific Southwest Region'],
	['insource:/43322816@N08/', 'PD-USGov-FWS', 'Photographs by U.S. Fish and Wildlife Service Northeast Region'],
	['insource:/43322816@N08/', 'PD-USGov-FWS', 'U.S. Fish and Wildlife Service Northeast Region'],
	['insource:/41464593@N02/', 'PD-USGov-FWS', 'U.S. Fish and Wildlife Service Southeast Region'],
	['insource:/33252741@N08/', 'PD-USGov-Military-National Guard', 'Files from the The United States National Guard Flickr stream'],
	['insource:/65191584@N07/', 'PD-USGov-Congress', 'UScapitol images from flickr'],
	['insource:/40927340@N03/', 'PD-USMC', 'Files from the U.S. Marine Corps Flickr stream'],
	['insource:/30884892@N08/', 'PD-USCG', 'Files from the U.S. Coast Guard Flickr stream'],
	['insource:/56594044@N06/', 'PD-USGov-Military-Navy', 'Files from the U.S. Navy Flickr stream'],
	['insource:/39513508@N06/', 'PD-USAF', 'Files from the U.S. Air Force Flickr stream'],['insource:/af.mil/', 'PD-USAF'],
	['insource:/navy.mil/', 'PD-USGov-Military-Navy'],
	['insource:/marines.mil/', 'PD-USMC'],
	['insource:/army.mil/', 'PD-USArmy'],
	['insource:/39736050@N02/', 'PD-USGov-FDA', 'Images from the United States Food and Drug Administration'],
	['insource:/75182224@N04/', 'PD-USGov-NPS', 'Files from the National Park Service Alaska Region Flickr stream'],
	['insource:/72578886@N08/', 'PD-USGov-NPS', 'Files from Arches NPS Flickr stream'],
	['insource:/78206310@N03/', 'PD-USGov-NPS', 'Files from Canyonlands NPS Flickr stream'],
	['insource:/77660923@N08/', 'PD-USGov-NPS', 'Files from Congaree NPS Flickr stream'],
	['insource:/57557144@N06/', 'PD-USGov-NPS', 'Files from DenaliNPS Flickr stream'],
	['insource:/56295925@N07/', 'PD-USGov-NPS', 'Files from Everglades NPS Flickr stream'],
	['insource:/43288043@N04/', 'PD-USGov-NPS', 'Files from Glacier National Park Service Flickr stream'],
	['insource:/50693818@N08/', 'PD-USGov-NPS', 'Files from Great Sand Dunes NPS Flickr stream'],
	['insource:/115357548@N08/', 'PD-USGov-NPS', 'Files from Joshua Tree National Park Flickr stream'],
	['insource:/99350217@N03/', 'PD-USGov-NPS', 'Files from Katmai NPS Flickr stream'],
	['insource:/61860846@N05/', 'PD-USGov-NPS', 'Files from Lassen Volcanic NPS Flickr stream'],
	['insource:/78037339@N03/', 'PD-USGov-NPS', 'Files from Mount Rainier NPS Flickr stream'],
	['insource:/127033241@N04/', 'PD-USGov-NPS', 'Files from RockyNPS Flickr stream'],
	['insource:/64710613@N03/', 'PD-USGov-NPS', 'Files from Saguaro NPS Flickr stream'],
	['insource:/67015038@N06/', 'PD-USGov-NPS', 'Files from Shenandoah NPS Flickr stream'],
	['insource:/80223459@N05/', 'PD-USGov-NPS', 'Files from Yellowstone NPS Flickr stream'],
	['insource:/54168808@N03/', 'PD-USGov-NPS', 'Files from Zion NPS Flickr stream'],
	['insource:/46658241@N06/', 'PD-USGov-USAID', 'USAID IMAGES'],
	['insource:/41937383@N07/', 'PD-USGov-Military-Army-USACE', 'Files from U.S. Army Corps of Engineers Detroit District Flickr stream'],
	['insource:/40704398@N05/', 'PD-USGov-Military-Army-USACE', 'Files from New York District, U.S. Army Corps of Engineers Flickr stream'],
	['insource:/52057813@N07/', 'PD-USGov-Military-Army-USACE', 'Files from U.S. Army Corps of Engineers Sacramento District Flickr stream'],
	['insource:/91981596@N06/', 'PD-USGov-BLM', 'Photographs by Bureau of Land Management'],
	['insource:/50169152@N06/', 'PD-USGov-BLM', 'Files from the Bureau of Land Management Oregon and Washington Flickr stream'],
	['insource:/55893585@N08/', 'PD-USGov-BLM', 'Photographs by the Nevada Bureau of Land Management'],
	['insource:/54593278@N03/', 'PD-USGov-DHS', 'Files from the U.S. Customs and Border Protection Flickr stream'],
	['insource:/39955793@N07/', 'PD-USGov-Military', 'Files from the U.S. Department of Defense Flickr stream'],
	['insource:/42310076@N04/', 'PD-USGov-Military', 'Files from the Chairman of the Joint Chiefs of Staff Flickr stream'],
	['insource:/78595004@N08/', 'PD-USGov-Military', 'Files from the U.S. OSD Deputy Secretary of Defense Flickr stream'],
	['insource:/68842444@N03/', 'PD-USGov-Military', 'Files from the U.S. Secretary of Defense Flickr stream'],
	['insource:/48445211@N06/', 'PD-USGov-ED', 'Files from the U.S. Department of Education Flickr stream'],
	['insource:/37916456@N02/', 'PD-USGov-DOE', 'Files from ENERGY.GOV Flickr stream'],
	['insource:/126057486@N04/', 'PD-USGov-DHS', 'Files from the U.S. Department of Homeland Security Flickr stream'],
	['insource:/9364837@N06/', 'PD-USGov-DOS', 'Files from the U.S. Department of State Flickr stream'],
	['insource:/47923257@N08/', 'PD-USGov-Treasury', 'Files from U.S. Department of the Treasury Flickr stream'],
	['insource:/130809712@N08/', 'PD-USGov-FBI', 'Files from the Federal Bureau of Investigation Flickr stream'],
	['insource:/50838842@N06/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Headquarters Flickr stream'],
	['insource:/49208525@N08/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Midwest Region Flickr stream'],
	['insource:/51986662@N05/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Mountain-Prairie Region Flickr stream'],
	['insource:/52133016@N08/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Pacific Region Flickr stream'],
	['insource:/54430347@N04/', 'PD-USGov-FWS', 'Files from the United States Fish and Wildlife Service Pacific Southwest Region Flickr stream'],
	['insource:/46536834@N08/', 'PD-USGov-FWS', 'Files from the US Fish and Wildlife Service - Recovery Act Team Flickr stream'],
	['insource:/54430347@N04/', 'PD-USGov-FWS', 'U.S. Fish and Wildlife Service Pacific Southwest Region'],
	['insource:/43322816@N08/', 'PD-USGov-FWS', 'Photographs by U.S. Fish and Wildlife Service Northeast Region'],
	['insource:/43322816@N08/', 'PD-USGov-FWS', 'U.S. Fish and Wildlife Service Northeast Region'],
	['insource:/41464593@N02/', 'PD-USGov-FWS', 'U.S. Fish and Wildlife Service Southeast Region'],
	['insource:/33252741@N08/', 'PD-USGov-Military-National Guard', 'Files from the The United States National Guard Flickr stream'],
	['insource:/65191584@N07/', 'PD-USGov-Congress', 'UScapitol images from flickr'],
	['insource:/40927340@N03/', 'PD-USMC', 'Files from the U.S. Marine Corps Flickr stream'],
	['insource:/30884892@N08/', 'PD-USCG', 'Files from the U.S. Coast Guard Flickr stream'],
	['insource:/56594044@N06/', 'PD-USGov-Military-Navy', 'Files from the U.S. Navy Flickr stream'],
	['insource:/39513508@N06/', 'PD-USAF', 'Files from the U.S. Air Force Flickr stream'],
	['insource:/35591378@N03/', 'PD-POTUS', 'Files from the Obama White House Flickr stream'],
	['insource:/nps.gov/', 'PD-USGov-NPS'],
 	['insource:/42600860@N02/', 'PD-USGov-NPS', 'Files from the U.S. National Parks Service Flickr stream'],
 	['insource:/www.dvidshub.net/', 'PD-USGov-DOD'],
	]

searchcore = 'incategory:"PD US Government" insource:/"{{PD-USGov}}"/ '

'''if len(argv)>1:
	searchstrings = searchstrings[int(float(argv[1])):]'''

scount = 0

#Expand templates
for searchstring in searchstrings:
	template = searchstring[1]
	tpage = pywikibot.Page(site, 'Template:' + template)
	if tpage.isRedirectPage():
		print Fore.CYAN + template, "→",
		template = tpage.getRedirectTarget().title()[9:]
		searchstring[1] = template
		print Fore.GREEN + template

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
			if re.search("diffusion", comments):
				print Fore.RED + "Appears to have been previously diffused", Fore.WHITE
				continue
			if len(searchstring)==3 and not re.search('Category:' + searchstring[2], html):
				html += "\n[[Category:" + searchstring[2] + "]]"
			action = "[[User:Fæ/code/PD-USGov]] diffusion '{}' → {}".format(searchstring[0], "{{" + searchstring[1] + "}}")
			pywikibot.setAction(action)
			ploop = 0
			while ploop<100:
				try:
					page.put(html)
					ploop = 100
				except Exception as e:
					ploop += 1
					print Fore.CYAN, ploop, Fore.RED, str(e), Fore.WHITE
					time.sleep(10 + min(170, 10*ploop))
