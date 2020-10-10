#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
# batchLOC.py
# Customized batch upload for Library of Congress images
# 
# There is dead code here! You can have quick and dirty
# or clean and never. ;-)
#
# Date: Mar 2014
# Author: Fae, http://j.mp/faewm
# Permissions: CC-BY-SA-4.0-UK
'''

import wikipedia, upload, sys, config, urllib2, urllib, re, string, time, catlib, pagegenerators, os.path, hashlib, pprint, subprocess
import json
import webbrowser, itertools

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from unidecode import unidecode
from BeautifulSoup import BeautifulSoup
from sys import argv
from sys import stdout
import collections
from time import sleep
from os import remove
from colorama import Fore, Back, Style
from colorama import init
init()
'''	Terminal colours:
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
'''

#	Colours only on mac
Red="\033[0;31m"     #Red
Green="\033[0;32m"   #Green
GreenB="\033[1;32m"	#Green bold
GreenU="\033[4;32m"	#Green underlined
Yellow="\033[0;33m"  #Yellow
Blue="\033[0;34m"    #Blue
Purple="\033[0;35m"  #Purpley
Cyan="\033[0;36m"    #Cyan
White="\033[0;37m"   #White

if len(sys.argv)>1:
		if sys.argv[-1]=="w":
				Red,White,Green,Cyan,Yellow='**','','','',''	#	Fix if in Windoze
		if sys.argv[1]=="help":
				print Yellow
				print '*'*60
				print """Optional parameters
#last <"w"> Switch off colours, to be windows console safe
"""+"*"*60,White
				sys.exit(0)

site = wikipedia.getSite('commons', 'commons')


def upchunk(source, filename, desc):
		token=site.getToken()
		print Fore.CYAN+"Edit token:", token
		# Cannot upload by url, have to cache file and point to chunks of it "chunk:"
		req = urllib2.urlopen(source)
		CHUNK = 16 * 1024
		while True:
				chunk = req.read(CHUNK)
				if not chunk: break
				params = {
          'action': 'upload',
          'token': token,
          'comment': desc,
          'filename': filename,
          'chunk': {'file': chunk},
          'stash': 1,
          'offset': 0,
						}
				
				print "Sending:", params
				data = wikipedia.query.GetData(params)
				print data
				if 'error' in data: # error occured
						errCode = data['error']['code']
						print data
		print Fore.WHITE



subs=[['%20',' '],['%28','('],['%29',')'],['%2C',','],['%3A',':']]
def pquote(s):
		s=urllib.quote(s)
		for c in range(len(subs)):
				s=re.sub(subs[c][0],subs[c][1],s)
		return s

def gettag(tag,name):
		if tag=='class':
				try:
						r=string.split(html,'class="'+name+'"')[1]
						r=string.split(r,'>')[1]
						r=string.split(r,'<')[0]
				except:
						return ''
				return r
		if tag=='td':
				try:
						r=string.split(html,'<tr><td>'+name+'</td><td>')[1]
						r=string.split(r,'</td>')[0]
				except:
						return ''
        	return r
		return ''

def trim(s):			#	Trim leading and trailing spaces
	return re.sub('^[\s\r\t\f\n_]*|[\s\r\t\f\n_]*$','',s)
def trimmore(s):	# Trim trailing or leading punctuation
		return re.sub('^[\.,;\-:\!]*|[\.,;\-:\!]*$','',s)

def up(filename, pagetitle, desc):
    url = filename
    keepFilename=True        #set to True to skip double-checking/editing destination filename
    verifyDescription=False    #set to False to skip double-checking/editing description => change to bot-mode
    targetSite = wikipedia.getSite('commons', 'commons')
    bot = upload.UploadRobot(url, description=desc, useFilename=pagetitle, keepFilename=keepFilename, verifyDescription=verifyDescription, targetSite = targetSite)
    bot.upload_image(debug=True)

def urltry(u):
	headers = { 'User-Agent' : 'Mozilla/6.0' } # Spoof header
	countErr=0
	x=''
	while x=='':
			try:
					req = urllib2.Request(u,None,headers)
					x = urllib2.urlopen(req)
					time.sleep(1)
			except:
					x=''
					countErr+=1
					if countErr>300: countErr=300	#	5 minutes between read attempts, eventually
					print Cyan,'** ERROR',countErr,'\n ** Failed to read from '+Yellow+u+Cyan+'\n ** Pause for '+str(countErr*1)+' seconds and try again ['+time.strftime("%H:%M:%S")+']',White
					time.sleep(1*countErr)
	return x

def htmltry(x,u):
		countErr=0
		r=True
		while r:
				try:
						return x.read()
				except:
						x=urltry(u)
						countErr+=1
						if countErr>200:
								p=300
						else:
								p=countErr*2
						print Cyan,'** ERROR',countErr,'\n ** Failed to read xml'
						if countErr==1:
								print Blue+'xml ='+str(x)
								print 'url ='+u+Cyan
						print ' ** Pause for '+str(p)+' seconds and try again'+White
						time.sleep(p)
				else:
						r=False
		return

def xmlfind(item):
		if data.find('<metadata name="'+item)>-1:
				return data.split('<metadata name="'+item+'" value="')[1].split('"')[0]
		else:
				return ''

def gettag(h):
  #<span class="link-11"><a href="/tag/thunderstorm" rel="tag" title="">Thunderstorm</a></span>
  t=re.split('href="/tag/[^"]*" rel="tag" title="">',h)
  for i in range(len(t)):
  	  t[i]=t[i].split('<')[0]
  t[0]=re.sub('^\s*|\s$','',t[0])
  if t[0]=='': t.pop(0)
  return ", ".join(t)

def getatt(t,h):
	if h.find('>'+t+':</th>')==-1: return ''
	r=re.split('<th scope="row"[^>]*>'+t+':</th>',h)[1].split('</td>')[0]
	r=re.sub('[\n\r\t\s]',' ',r)
	r=re.sub('\s+',' ',r)
	return re.sub('^\s*|<[^>]*>|\s*$','',r)

def getcat(h):
  # <div class="item-list"><ul><li><a href="/type/natural">Natural</a></li><li><a href="/type/characteristic">Characteristic</a></li></ul></div>
  if h.find('<div class="terms">Type</div>')==-1: return '[[Category:Pdsounds.org]]'
  r=h.split('<div class="terms">Type</div>')[1]
  r=r.split('class="item-list"><ul>')[1]
  r=r.split('</a></li></ul>')[0]
  r=r.split('</a></li>')
  c=''
  for i in range(len(r)):
    r[i]=re.sub('<[^>]*?>','',r[i])
  return ", ".join(r)

def dupcheck(ff):	#	Using the SHA1 checksum, find if the file is already uploaded to Commons
		df=urllib2.urlopen(ff)
		#df=open(ff,'rb')
		notread=True	#	Try to deal with socket.timeout
		while notread:
			notread=False
			try:
				sha1 = hashlib.sha1(df.read()).hexdigest()
			except:
				notread=True
				print Red+"Trouble getting SHA1 for file, trying again in 5 seconds."
				time.sleep(5)
		#print Cyan+'SHA1='+sha1
		u="http://commons.wikimedia.org/w/api.php?action=query&list=allimages&format=xml&ailimit=1&aiprop=sha1&aisha1="+sha1
		notread=True
		while notread:
				notread=False
				try:
						x=urllib2.urlopen(u)
				except:
						notread=True
						print Red+"Trouble reading",u
						time.sleep(5)
		xd=x.read()
		x.close()
		if xd.find("<img")>-1:
				t=xd.split('title="')[1].split('"')[0]
				return True,t
		return False,''

# Check if a file title is already used on commons
def nameused(name):
		u="http://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&format=xml&titles=File:"+urllib.quote(name)
		ux=urltry(u)
		x=htmltry(ux,u)
		if x.find('<imageinfo>')>-1:
				return True
		return False

def trimtags(s):
	return trim(re.sub('<[^>]*?>','',s))

def titlecase(s):
	s=re.sub('&#0?39;',"'",s)
	s=re.sub('&amp;','and',s)
	s=re.sub(':','-',s)
	words=s.split(" ")
	smallwords=['at','the','of','by','a','during','work','on','in','and']
	bigwords=['UK','US','USA','U\.S\.','H\.M\.S\.','HMS', 'RAF', 'R\.A\.F\.', 'YWCA', 'YMCA']
	for i in range(len(words)):
	  staybig=False
	  for j in bigwords:
				if re.search('^'+j+'[,\.;\(\)\-]?',words[i]):
						staybig=True
						continue
	  if not staybig:
				words[i]=words[i][0:1]+words[i][1:].lower()
	  else:
				continue
	  if i==0:
			continue
	  else:
			for j in smallwords:
				if words[i].lower()==j: words[i]=words[i].lower()
				continue
	return ' '.join(words)

#	*** Grab description ***
def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def twodigits(d):
		if len(d)>1: return d
		return "0"+d

def getdesc(html):
		soup=BeautifulSoup(html)
		try:
				image=soup.findAll("img")[-1]
		except:
				return ''
		attrib=html.split("If you are going to publish, redistribute this image on the Internet place this link:")[1].split("</td>")[0]
		title=attrib.split("title=&quot;")[1].split("&quot")[0]
		site=attrib.split("href=&quot;")[1].split("&quot")[0]
		try:
				author=re.sub("\n","",urllib.quote(attrib.split("&gt; by ")[1].split("</em")[0], " ,").encode('ascii','ignore'))
		except:
				author="Public Domain Images"
		return '{{information\n| description = {{en|1=<br/>\n:''Image title: '+image['title']+'\n:Image from Public domain images website, '+site+"}}\n| source = "+image['src']+"\n| author = "+author+'\n| date = Not given\n*Transferred by [[User:{{subst:User:Fae/Fae}}|]] on {{subst:today}}\n| permission = This file is in public domain, not copyrighted, no rights reserved, free for any use. You can use this picture for any use including commercial purposes without the prior written permission and without fee or obligation.\n}}\n=={{int:license}}==\n{{PD-author|1='+author+'}}\n[[Category:Images uploaded by {{subst:User:Fae/Fae}}]]\n[[Category:Public-domain-image.com]]'+allcat, re.sub("\s{2,}"," ",image['title'].encode('ascii','ignore'))+'.jpg', image['src']

nocats=['India', 'England', 'Africa', 'Europe', 'France',
				'Great Britain', 'China']
gocats=[]
def catexists(cat):	#	Does this Commons category exist? It may be worth checking for {{categorise}} before using it
		# Cats to avoid
		if len(cat)<2: return False
		for nocat in nocats:
				if cat==nocat:
						return False
		urlpath="http://commons.wikimedia.org/w/api.php?action=query&prop=info&format=xml&titles=Category:"+urllib.quote(cat)
		url=urltry(urlpath)
		xml=htmltry(url,urlpath)
		if re.search('missing=""',xml):
				return False
		else:
				# Check if a diffusion category
				for gocat in gocats:
						if cat==gocat:
								return True
				cat_page = wikipedia.Page(site, "Category:" + cat).get()
				if re.search(r"\{\{[Cc]ategorize\}\}", cat_page):
						nocats.append(cat)
						print Fore.RED+"Category check of", cat, "showed diffusion category so ignoring suggestion.", Fore.WHITE
						return False
				else:
						gocats.append(cat)
				return True

plist=[]

def exists(url):	#	Does this Webpage exist?
		try:
				f = urllib2.urlopen(urllib2.Request(url))
				return True
		except:
				#print Red+"Could not find",url,White
				return False

def uptry(source,filename,desc):
		countErr=0
		r=True
		while r:
				try:
						up(source,filename,desc)
						return
				except:
						countErr+=1
						if countErr>200:
								p=300
						else:
								p=countErr*5
						print Cyan,'** ERROR Upload failed'
						print ' ** Pause for '+str(p)+' seconds and try again'+White
						time.sleep(p)
		return

def createcat(cat,txt):
		wikipedia.setAction("Create category")
		p=wikipedia.Page(site,"Category:"+cat)
		print Green,"Creating category",cat,White
		p.put(txt)
		return

plist=[]
def virinSearch(v):
		vcount=0
		countErr=0
		loop=True
		while loop:
				try:
						vgen = pagegenerators.SearchPageGenerator(v, namespaces = "6")
						for vPage in vgen:
								plist.append(vPage.title())
								vcount+=1
						loop=False
				except:
						loop=True
						countErr+=1
						print Red+"Problem running search, sleeping for",countErr,"seconds",Fore.WHITE
						time.sleep(countErr)
				if countErr>30:
						loop=False
						vcount=-1
		return vcount


def boxnotice(s,center=False,ctext=Fore.GREEN,cbox=Fore.YELLOW):
		sArr=s.split("\n")
		width=0
		for ss in sArr:
				if len(ss)>width-2: width=len(ss)+2
		#print os.name
		ascii=False
		if os.name=="nt":
				ascii=True
		if ascii:
				ulc,urc,lnc,blc,brc,llc="+","+","-","+","+","|"
		else:
				ulc,urc,lnc,blc,brc,llc=u"\u250F",u"\u2513",u"\u2501",u"\u2517",u"\u251B",u"\u2503"
		print cbox+ulc+lnc*width+urc		#	http://en.wikipedia.org/wiki/Box-drawing_character
		for ss in sArr:
				if len(ss)<width-3 and center:
						ss=" "*int((width-2-len(ss))/2)+ss
				print cbox+llc+" "+ctext+ss+" "*(width-1-len(ss))+cbox+llc
		print cbox+blc+lnc*width+brc,Fore.WHITE


def ansearch(mysoup,mystring,href=False):
		if href:
				r=mysoup.find('a',{'href':re.compile(mystring)})['href']
		else:
				r=mysoup.find('a',{'href':re.compile(mystring)}).string
		if len(r)==0 or r is None:
				return ""
		return r

def make_unique(lst):
    if len(lst) <= 1:
        return lst
    last = lst[-1]
    for i in range(len(lst) - 2, -1, -1):
        item = lst[i]
        if item == last:
            del lst[i]
        else:
            last = item

'''
*** SCRAPE FILENAMES ***
'''

# Custom scripts for scraping this website

# Main loop

skip=0
if len(argv)>1:
		skip=int(float(argv[1]))

picurl = "https://picasaweb.google.com/111909687173441673035/NSS2014"

if len(argv)>2 and len(argv[2])>2:
		picurls=argv[2].split(' ')

usercat=''
if len(argv)>3:
		usercat = argv[3]

if len(argv)>4:
		test=1
else:
		test=0

print Fore.GREEN+"*"*70
print "Picasa batch upload (put spaces between album identifiers)"
print argv[0]
print "[1] skip =",skip
print "[2] url =", picurls
print "[3] test =",test
print '''Example urls:
https://picasaweb.google.com/111909687173441673035/NSS2014"
'''
print Fore.GREEN+"*"*70

ccount = 0
for picurl in picurls:
		count = 0
		if not re.search("picasaweb.google", picurl):
				picurl = "https://picasaweb.google.com/"+picurl
		gitems = BeautifulSoup(htmltry(urltry(picurl), picurl)).find('div', id="lhid_feedview").noscript.findAll('a', href=re.compile("https://picasaweb.google.com/lh/photo/.*"))
		gitems = list(set([a['href'] for a in gitems]))
		print len(gitems)
		import ast, datetime
		for a in gitems:
				ccount+=1;count+=1; skipthis = False
				if ccount < skip: continue
				print Fore.CYAN, ccount, a, Fore.WHITE
				detail = BeautifulSoup(htmltry(urltry(a), a).split('id="lhid_album_title"')[1]).findAll('script')[1].text.split('\n')[10]
				detail = ast.literal_eval(detail)[0]['preload']
				lic    = detail['feed']['cc']
				album  = detail['feed']['albumInfo'][0]
				author = detail['feed']['author'][0]
				title  = detail['feed']['title']
				cap    = detail['feed']['htmlCaption']
				source = detail['feed']['media']['thumbnail'][0]['url']
				#pprint.pprint(detail['feed'])
				date = datetime.datetime.fromtimestamp(int(detail['feed']['timestamp'])/1000).strftime('%Y-%m-%d %H:%M:%S')
				if re.search("DSC", title):
						filename = ''+trim(album['title']) +' '+ str(count) + '.jpg'
				else:
						filename = ''+trim(re.sub('\.(JPG|jpg)', '', title))+ ' '+ album['title'] + ' ' + str(count) + '.jpg'
				subs = [
						[r"[\t:]", " "],
						["#", "-"],
						[r"\s{2,}", " "],
						["IMG_?", ""],
						[r"[\[\{]","("],
						["「","("],
						[r"[\}\]]",")"],
						["」",")"],
						[r" _", " "],
						]
				filename = re.sub("　", " ", filename)
				filename = re.sub(" _", " ", filename)
				for s in subs:
						filename = re.sub(s[0], s[1], filename)
				print Fore.GREEN, filename, Fore.WHITE
				if not re.search("ATTRIBUTION_SHARE_ALIKE", lic):
						skipthis = True
						print Fore.RED, "Licence given as", lic, "skipping...", Fore.WHITE
				else:
						lic = "{{cc-by-sa-3.0}}"
				d="\n=={{int:filedesc}}==\n{{Information"
				d+= "\n|description = {{en|1=<br/>\n:''Title'' "+ title
				d+= "\n:''Album'' "+ album['title']
				if len(cap)>1:
						d+= '\n:'+ cap
				elif usercat!='':
						d+= '\n:' + usercat
				d+='}}'
				d+='\n|author = ['+ author['uri'] + ' ' + author['name'] + ']'
				d+="\n|source = \n:''Image'' " + source
				d+="\n:''Gallery'' " + a.encode('UTF-8')
				d+='\n|date =' + date
				d+="\n}}\n\n=={{int:license-header}}==\n"
				d+= lic
				d+='\n\n{{picasareview|{{subst:User:Fae/Fae}}|~~~~~}}'
				d+= '\n{{subst:chc}}'
				d+= '\n\n[[Category:Images uploaded by {{subst:User:Fae/Fae}}]]'
				if usercat!='':
						d+= '\n[[Category:'+usercat+']]'
				if not skipthis:
						# Quick check of filename in use - these should be unique
						if nameused(filename):
								print Red+' Filename found', White
								continue
						# Check if image is a duplicate on Commons
						try:
								duplicate,duptitle = dupcheck(source)
						except:
								print Red+"Problem when running the duplicate check for",source,White
								time.sleep(10)
								try:
										duplicate,duptitle = dupcheck(source)
								except:
										print Red+"Failed on second try, giving up and skipping"
										continue
						if duplicate and test==0:
								print Red+'File is already on Commons as', duptitle, White
								time.sleep(2)
								continue
						if test==0:
								uptry(source, (filename).decode('utf-8'), d)
						else:
								print Fore.YELLOW+d, Fore.WHITE
								print Fore.RED+"** Test mode, not uploading **", Fore.WHITE
						#print Fore.YELLOW,d, Fore.WHITE
						# Nice pause for human oversight
						lag=0
						if test>0: lag=0
						for i in range(lag):
								stdout.write("\r%d " % (lag-i))
								stdout.flush()
								sleep(3)
						stdout.write("\r  ")
						stdout.flush()
						stdout.write("\r")
