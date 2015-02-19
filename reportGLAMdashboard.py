#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
# reportGLAMdashboard.py

A generalized tool based on Fae's experience of reporting needs
and informal discussion with the GLAM/Commons community
http://commons.wikimedia.org/wiki/User:Faebot/GLAM_dashboard

There is poorly designed and dead code here! You can have quick and dirty
or clean and never. It's the wiki-way, probably. ;-)

Date: Nov 2014
Author: Fae, http://commons.wikimedia.org/wiki/User:Fae
Permissions: CC-BY-SA-4.0

This tool was produced by Fae as an unpaid volunteer, without support
from any organization and should not be claimed to be part of any sponsored
project.
'''

import urllib
import pywikibot
import re
import catlib, pagegenerators
import MySQLdb

def improvement(cat_list):
		cursor.execute("""
SELECT
	page_title,
	CONCAT(REPLACE(gil_wiki,'wiki',''), ':',  gil_page_title) AS link
FROM page
INNER JOIN globalimagelinks ON page_title = gil_to
INNER JOIN categorylinks ON page_id=cl_from AND cl_to IN (""" + cat_list + """)
INNER JOIN image ON img_name=page_title
WHERE
	gil_page_namespace=""
	AND RIGHT(gil_wiki,4)='wiki'
	AND gil_wiki!='wikidata'
GROUP BY page_title
HAVING COUNT(gil_page_title)=1
ORDER BY RAND()
LIMIT 10;
		""")
		gallery=[]
		for page, link in cursor.fetchall():
				gallery.append("File:"+page +"|<center>[[:"+ re.sub('_',' ',re.sub('data:','wikidata:', link)) +"]]</center>")
		report = "Ten randomly selected files with a single mainspace use on Wikimedia projects:\n<gallery>\n"+"\n".join(gallery)+"\n</gallery>"
		print "Working out mincat"
		cursor.execute("""
				SELECT COUNT(c4.cl_to)
				FROM page p2
				JOIN categorylinks c3 ON page_id=c3.cl_from
				JOIN categorylinks c4 ON page_id=c4.cl_from
				WHERE c4.cl_to IN (""" + cat_list + """)
				AND p2.page_namespace=6
				GROUP BY p2.page_title
				ORDER BY COUNT(c4.cl_to)
				LIMIT 1;""")
		for c in cursor.fetchall():
				mincats = c[0]
		#print "*** mincats is", int(float(mincats))
		mincats = int(float(mincats))
		cursor.execute("""
SELECT p1.page_title, page_id
FROM page p1
JOIN categorylinks c1 ON p1.page_id=c1.cl_from
JOIN categorylinks c2 ON p1.page_id=c2.cl_from
WHERE 
c1.cl_to IN (""" + cat_list + """)
AND page_namespace=6
GROUP BY p1.page_title
HAVING COUNT(c2.cl_to)="""+str(mincats)+""" LIMIT 10;""")
		gallery=[]
		for page, page_id in cursor.fetchall():
				gallery.append("File:"+page +"\n")
		report += "\nUp to ten randomly selected files with the lowest category counts in the project:\n<gallery>\n"+"\n".join(gallery)+"\n</gallery>"
		return report

def most_edited(cat_list):
		cursor.execute("""SELECT DISTINCT page_title, (SELECT COUNT(rev_timestamp) FROM revision WHERE page_id=rev_page) AS Edits
		FROM page
		JOIN categorylinks ON page_id=cl_from
		JOIN revision ON page_id=rev_page
		WHERE cl_to IN (""" + cat_list + """)
			AND page_namespace=6
		ORDER BY (SELECT COUNT(rev_timestamp) FROM revision WHERE page_id=rev_page) DESC
		LIMIT 24;""")
		
		table = []
		for page_title, edits in cursor.fetchall():
			table.append("File:"+page_title+"|<center>"+ str(edits) +" edits</center>")
		
		table = "<gallery>\n"+"\n".join(table) +"\n</gallery>"
		return table

def largest(cat_list):
		cursor.execute("""
		SELECT CONCAT("File:",img_name) AS File,
				 CONCAT( ROUND(img_width*img_height/1000000), " MP<br><small>", img_width, "x", img_height, " pixels</small>" ) AS Size
				 FROM image
				 JOIN page ON page_title=img_name
				 JOIN categorylinks ON page_id=cl_from
				 WHERE cl_to IN (""" + cat_list+""")
				 AND img_width>0
				 ORDER BY img_width*img_height DESC
				 LIMIT 24;
		""")
		
		table = []
		for File, Size in cursor.fetchall():
			table.append(File+"|<center>"+Size+"</center>")
		table="<gallery>\n"+"\n".join(table)+"\n</gallery>"
		return table
		
'''
SELECT CONCAT("File:",img_name) AS File,
CONCAT( ROUND(img_width*img_height/1000000), " MP<br><small>", img_width, "x", img_height, " pixels</small>" ) AS Size
FROM image
JOIN page ON page_title=img_name
JOIN categorylinks ON page_id=cl_from
WHERE cl_to IN ("Xeno-canto")
ORDER BY img_width*img_height DESC
LIMIT 24;
'''

def volunteers(cat_list):
		cursor.execute("""
		SELECT DISTINCT rev_user_text,
			COUNT(page_title) AS edit_count
		FROM categorylinks
		RIGHT JOIN page ON cl_from = page_id 
		LEFT JOIN revision ON page_id = rev_page
		WHERE page_namespace=6
			AND cl_to IN (""" + cat_list + """)
			AND rev_user_text NOT REGEXP '[Bb]ot'
		GROUP BY 1
		HAVING edit_count>0 
		ORDER BY 2 DESC;"""
		)
		
		table = []
		for userx, count in cursor.fetchall():
				table.append([count, "<abbr title='{} edits'>[[User talk:".format(count) + userx + "|" +userx +"]]</abbr>"])
		
		result = "{| class='wikitable sortable'\n!Edits!!#!!Volunteers"
		r = [u[1] for u in table if u[0]>999]
		if len(r)>0:
				result+= "\n|-\n|1000+||" + str(len(r)) +"||"+"{{middot}}".join(r)
		r = [u[1] for u in table if u[0]>99 and u[0]<1000]
		if len(r)>0:
				result+= "\n|-\n|100+ ||" + str(len(r)) +"||"+"{{middot}}".join(r)
		r = [u[1] for u in table if u[0]>9 and u[0]<100]
		result+= "\n|-\n|10+  ||" + str(len(r)) +"||"+"{{middot}}".join(r)
		r = [u[1] for u in table if u[0]<10]
		result+= "\n|-\n|     ||" + str(len(r)) +"||"+"{{middot}}".join(r)
		result+= "\n|}"
		
		return result
'''
SELECT DISTINCT rev_user_text,
COUNT(page_title) AS edit_count
FROM categorylinks
RIGHT JOIN page ON cl_from = page_id 
LEFT JOIN revision ON page_id = rev_page
WHERE page_namespace=6
AND cl_to IN ('Media_contributed_by_Zentralbibliothek_Solothurn')
AND rev_user_text NOT REGEXP '[Bb]ot'
GROUP BY 1
HAVING edit_count>0 
ORDER BY 2 DESC;
'''

def glamorous_list(cat_list):
		query="""
SELECT
	page_title,
	count(gil_page_title) AS gilcount,
	GROUP_CONCAT(CONCAT(gil_wiki,' : ',IF(gil_page_namespace!='',CONCAT(gil_page_namespace, ':'),gil_page_title)) SEPARATOR ' // ') AS list FROM page
JOIN categorylinks ON page_id=cl_from
JOIN globalimagelinks ON page_title=gil_to
WHERE cl_to IN ("""+cat_list+""")
GROUP BY page_title
ORDER BY gilcount DESC
LIMIT 24;"""
		cursor.execute(query)
		gallery="<gallery>\n"
		for title, gilcount, concat in cursor.fetchall():
				gallery+= 'File:'+title +'|<abbr title="'+ concat + '">'+ str(gilcount) +'</abbr>\n'
		gallery+='</gallery>'
		return gallery

def popular_categories(cat_list):
		query="""
SELECT c.cl_to AS category,
COUNT(DISTINCT page_id) AS total
FROM page
INNER JOIN categorylinks AS c ON page_id=c.cl_from AND c.cl_to NOT IN (""" + cat_list +""")
INNER JOIN categorylinks AS cc on page_id=cc.cl_from AND cc.cl_to IN ("""+ cat_list +""")
WHERE c.cl_to NOT REGEXP "Files_from|CC-BY|Files_with|test_|Uploaded_with|Self-pub|Items_with_OTRS|GFDL|FAL|PD-|uploaded_by_|Flickr_images_reviewed|Flickr_images_uploaded"
GROUP BY c.cl_to
HAVING total>1
ORDER BY COUNT(page_id) DESC
LIMIT 100;
"""
		cursor.execute(query)
		table = "{{flatlist|"
		for cat, total in cursor.fetchall():
				table+="\n*[[:Category:"+re.sub("_"," ",cat)+"|]]"+" ({:,})".format(total)
		table+="\n}}"
		return table

def child_catcher(category, recursive): # From seed category return children list to 2 levels
		cat = catlib.Category(site, category)
		gen = pagegenerators.SubCategoriesPageGenerator(cat, recurse=recursive)
		children = []
		for c in gen:
				children.append(c.title())
		children.append(category)
		return children

def get_projects():
		source = pywikibot.Page(site, 'User:Faebot/GLAM dashboard').get()
		source = source.split('\n==Requests==')[1].split('\n==')[0]
		projects = []
		for p in re.split(r'\n\*[^\*]', source):
				#if re.search('EAGLE', p): continue # DEBUG
				cat = re.sub('\[\[:?|\|.*|\]\]', '', p.split('\n')[0])
				rep = re.sub('^[ \*]*|\[\[:?|\|.*|\]\]', '', p.split('\n')[1])
				if cat[:3]!='Cat': continue
				recursive=0
				if re.search(r"[Rr]ecursive", " ".join(p.split('\n')[2:])):
						if re.search(r"[Rr]ecursive \d", " ".join(p.split('\n')[2:])):
								recursive=int(float(re.findall(r"[Rr]ecursive (\d)", " ".join(p.split('\n')[2:]))[0]))
								if recursive>6: recursive=6
						else:
								recursive=2
				projects.append([cat, rep, recursive])
		return projects

def index(bpage):
		bpage = re.sub("_", " ", bpage)
		text=""
		# Ensure any new reports are added here
		for sub in ["popular categories", "wikimedia usage", "volunteers", "most edited", "largest", "improvement"]:
				text += "* [[:" + bpage + "/" + sub + "|" + sub[0:1].upper() + sub[1:] + "]]\n"
		return text.encode('utf-8', 'ignore')

def put_report(report, spage, action, imagecheck=True):
		report = report.decode('utf-8', 'ignore')
		page = pywikibot.Page(site, spage)
		'''try:
				html = page.get()
				if len(html)==len(report):	# There may be some real changes lost, but most of non-length changes are trivial shuffling
						return
				if imagecheck:
						imgs = set(re.findall(r"File:[^\|\]]*\(jpe?g|JPE?G|og[gv]|OG[GV]|svg|SVG|tiff?|TIFF?|gif|GIF)", html))
						rimgs = set(re.findall(r"File:[^\|\]]*\(jpe?g|JPE?G|og[gv]|OG[GV]|svg|SVG|tiff?|TIFF?|gif|GIF)", report))
						if imgs.issubset(rimgs) and rimgs.issubset(imgs):
								return
		except:
				pass'''
		cats = [c.title() for c in page.categories()]
		for cat in cats:
				if not re.search(re.escape(cat), report):
						report += '\n[[' + cat + ']]'
		pywikibot.setAction(action)
		page.put(report)
		return

def main():
		projects = get_projects()
		for p in range(len(projects)):
				if projects[p][2] == False:
						projects[p][0] = [projects[p][0]]
						continue
				projects[p][0] = child_catcher(projects[p][0], projects[p][2])
		# Make one d/b connection for all queries - more efficient I believe
		conn = MySQLdb.connect(
				read_default_file = "~/replica.my.cnf",
				host = "commonswiki.labsdb",
				db = "commonswiki_p",
				)
		global cursor
		cursor = conn.cursor()
		for project in projects:
				cscats = ('"' + '","'.join([re.sub(" ","_",c[9:]) for c in project[0]]) + '"').encode('utf-8')
				put_report(improvement(cscats), project[1] + "/improvement", "GLAM dashboard improvement suggestions")
				put_report(popular_categories(cscats), project[1] + "/popular_categories", "GLAM dashboard update popular categories", imagecheck=False)
				put_report(glamorous_list(cscats), project[1] + "/wikimedia_usage", "GLAM dashboard update usage")
				put_report(volunteers(cscats), project[1] + "/volunteers", "GLAM dashboard update volunteer list", imagecheck=False)
				put_report(most_edited(cscats), project[1] + "/most_edited", "GLAM dashboard update most edited")
				put_report(largest(cscats), project[1] + "/largest", "GLAM dashboard update largest")
				put_report(index(project[1]), project[1] + "/index", "GLAM dashboard index", imagecheck=False)
		conn.close()

if __name__ == "__main__":
		usage = u'Usage:\tAsk Fae'
		site = pywikibot.getSite('commons', 'commons')
		main()
