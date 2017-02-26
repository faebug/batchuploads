#!/usr/bin/python
# -*- coding: utf-8 -*-
NOTICE = '''
Sustainable Sanitation Alliance (SuSanA)
Flickr batch upload.

Date: Apr 2014, Feb 2015,
 2015 July: added pools, posted to Flickr date, license checks
 2017 February: convert to pywikibot.core
 
Author: Fae, http://j.mp/faewm
Code license: CC-BY-SA-4.0
'''

import pywikibot, upload, sys, urllib2, urllib, re, string, time, os
import hashlib
from pywikibot.compat import catlib
from pywikibot import pagegenerators
import datetime
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

site = pywikibot.getSite('commons', 'commons')

def up(source, pagetitle, desc, comment):
	if source[:4] == 'http':
		source_url=source; source_filename=None
	else:
		source_url=None; source_filename=source
	
	site.upload(pywikibot.ImagePage(site, 'File:' + pagetitle),
		source_filename=source_filename, 
		source_url=source_url,
		comment=comment, 
		text=desc, 
		watch=False, 
		ignore_warnings=False,
		chunk_size=1048576, 
		_file_key=None, 
		_offset=0, 
		_verify_stash=None,
		report_success=None)

    		
def urltry(u, headers = { 'User-Agent' : 'Mozilla/5.0' } ):
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

class TooBigException(Exception):
    pass

def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)/ (1024 * 1024)
    if progress_size>100:
    		raise TooBigException
    speed = int(progress_size * 1024 / (duration))
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write("\r%d MB, %d KB/s, %d seconds passed" %
                    (progress_size, speed, duration))
    sys.stdout.flush()

def urlretrievetry(src, loc):
		loop=True
		lc=0
		while loop:
				try:
						urllib.urlretrieve(src, loc, reporthook)
						return True
				except TooBigException:
						loop=False
						return False
				except Exception, err:
						lc+=1
						if lc<5:
								print Fore.RED+"Retrieve error from {0}".format(src)
								print Fore.YELLOW, "Attempt {1}, error {0}".format(err, lc), Fore.WHITE
						else:
								print Fore.RED+"Had",lc-1,"attempts now, giving up",Fore.WHITE
								loop=False
								return False


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
				print ff
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

def trim(s):
	return re.sub(r"^[\s_]*|[\s_]*$", "", s)

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

nocats=set(['India', 'England', 'Africa', 'Europe', 'France',
				'Great Britain', 'China', 'Germany', 'Economics',
				'Journalism', 'Uganda', 'Landscapes',
				'Western', 'Project', 'Kenya',
				])
gocats=set()
def catdiffusion(cat): # test given cat is gocat or nocat
		if cat in gocats: return True
		if cat in nocats: return False
		cat_page = pywikibot.Page(site, "Category:" + cat)
		if not cat_page.exists():
				nocats.add(cat)
				return False
		cat_page=cat_page.get()
		if re.search(r"\{\{[Cc]ategorize\}\}", cat_page):
				nocats.add(cat)
				print Fore.RED+"Category check of", cat, "showed diffusion category so adding to nocat set from here on.", Fore.WHITE
				return False
		else:
				gocats.add(cat)
				print Fore.GREEN+"Category check of",cat,"looks okay, adding to gocat set from here on.", Fore.WHITE
				return True
		
plist=[]

def exists(url):	#	Does this Webpage exist?
		try:
				f = urllib2.urlopen(urllib2.Request(url))
				return True
		except:
				#print Red+"Could not find",url,White
				return False

def uptry(source,filename,desc,comment):
		countErr=0
		r=True
		while r:
				try:
						up(source,filename,desc,comment)
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
		pywikibot.setAction("Create category")
		p=pywikibot.Page(site,"Category:"+cat)
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
				except Exception, e:
						loop=True
						countErr+=1
						print Fore.YELLOW, time.strftime("%d %b @%H:%M:%S"), Fore.WHITE
						print Fore.RED+"Error [{}]".format(str(e))
						print Fore.RED+"Problem running search ['{}' attempted {} times], sleeping for".format(v, countErr),countErr,"seconds",Fore.WHITE
						time.sleep(countErr)
				if countErr>120:
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

'''
*** MAIN ***
'''

import flickrapi

# Hey, if you are reusing this script, you must set up a Flickr API key

api_key = 'a16b575a7753907bcea97a2b22104a57'
api_secret = open('scripts/flickr_api_secret.txt', 'r').read()

flickr = flickrapi.FlickrAPI(api_key, api_secret)

nsid = "23116228@N07" # Sanitation SSA

licenses = {}
for l in flickr.photos_licenses_getInfo()[0].findall('license'):
		licenses[l.get('id')] = l.get('name')

startpage = 1
if len(argv)>1:
		startpage = int(float(argv[1]))

endpage = 1000
if len(argv)>2:
		endpage = int(float(argv[2]))

print Fore.GREEN+"*"*60
print Fore.YELLOW + NOTICE, Fore.GREEN
print argv[0]
print "[1] Start page", startpage
print "[2] End page", endpage
print Fore.GREEN+"*"*60, Fore.WHITE

uploadcount=0
count = 0
for ploop in range(startpage, endpage):
  for page in flickr.photos_search(user_id=nsid, per_page='20', content_type='1', page=str(ploop)):
		for photo in page:
				count += 1
				print Fore.CYAN, count, Fore.YELLOW, ploop, Fore.BLUE,"-"*70
				record = {}
				record['count']=count
				pid = photo.get('id')
				record['id'] = pid
				info = flickr.photos_getInfo(user_id=nsid, photo_id=pid, api_key=api_key)
				record['licence'] = licenses[info[0].get('license')]
				licgood=False
				if record['licence'] == 'Attribution License':
					record['licence'] = '{{CC-BY-2.0}}'
					licgood=True
				if record['licence'] == 'Attribution-ShareAlike License':
					record['licence'] = '{{CC-BY-SA-2.0}}'
					licgood=True
				if record['licence'] == 'No known copyright restrictions':
					record['licence'] = '{{Flickr-no known copyright restrictions}}'
					licgood = True
				if record['licence'] == 'Public Domain Dedication (CC0)':
					record['licence'] = '{{CC0}}'
					licgood = True
				if record['licence'] == 'Public Domain Mark':
					record['licence'] = '{{PD-user|1=' + record['username'] +'}}'
					licgood = True
				if not licgood:
					print Fore.RED, "Licence problem. The licence found is", record['licence'], Fore.WHITE
					continue
				
				record['originalformat'] = info[0].get('originalformat')
				contexts = flickr.photos_getAllContexts(photo_id = pid)
				record['title'] = info[0][1].text
				try:
						if re.search("Group Invite", record['title']):
								print Fore.RED, record['title']
								print " Skipping, found 'Group Invite' in title", Fore.WHITE
								continue
				except TypeError:
						print "TypeError when reading title in", pid, "title given as", record['title']
						record['title']=''
				record['filename'] = record['title'] + " ("+ record['id'] + ").jpg"
				record['description'] = info[0].find('description').text
				#try:
				#	record['description'] = linktowiki(record['description'])
				#except TypeError:
				#		record['description'] = ''
				if record['description'] is None:
						record['description']=''
				record['date'] = info[0].find('dates').get('taken')
				record['url'] = info[0].find('urls').find('url').text
				loop = True
				while loop:
						try:
								sizes = flickr.photos_getSizes(photo_id = pid)
								loop=False
						except Exception, e:
								print Fore.RED+"Exception on flickr.photos_getSizes"
								print ' '+str(e), Fore.WHITE
				sizes = sizes[0].findall('size', {"label":'Original'})[-1]
				record['source'] = sizes.get('source')
				record['height'] = sizes.get('height')
				record['width'] = sizes.get('width')
				tags = [re.sub("[=#]", " ", t.get('raw')) for t in info[0].find('tags').findall('tag')]
				record['tags'] = tags
				cats = []
				for tag in tags:
						try:
								if len(tag)>4:
										cattest=(tag[0:1].upper() + tag[1:]).decode('utf-8')
										if catdiffusion(cattest):
												cats.append(cattest)
						except Exception, e:
								print Fore.RED, str(e)
								print " " + tag.encode('utf-8','ignore'), Fore.WHITE
				
				record['sets'] = []
				record['sets'] = [s.get('title') for s in contexts.findall('set')]
				record['pools']= [s.get('title') for s in contexts.findall('pool')]
				record['posted'] = datetime.datetime.fromtimestamp(float(info[0].find('dates').get('posted'))).strftime('%Y-%m-%d')
				record['nsid'] = info[0].find('owner').get('nsid')
				record['username'] = info[0].find('owner').get('username')
				record['realname'] = info[0].find('owner').get('realname')
				record['location'] = ''
				try:
						geo = flickr.photos_geo_getLocation(photo_id = pid)[0].find('location')
						record['location'] = '{{Location|1=' + geo.get('latitude')+'|2='+ geo.get('longitude') + '}}'
				except Exception, e:
						print Fore.RED, str(e), Fore.WHITE
				if record['originalformat'] != "jpg":
						print Fore.RED, record['title'], "\n Does not match filtered items, skipping.", Fore.WHITE
						continue
				subs = [
						['[\/\|:#]', '-'],
						['&[Cc].?;','etc'],
						['& ', 'and '],
						['[\[\{]', '('],
						['[\]\}]', ')'],
						['\.;|,;|;;', ';'],
						[' ; ', '; '],
						['[_ ]{2,}', ' '],
						['-{2,}', '-'],
						]
				if re.search("^CIMG|^SAM_|^GEDC|^SONY DSC|^_MG_|^Image|^\d{6}|^IMG|^DSC", record['title']) or len(record['title'])<3:
						print Fore.RED, "Fixing bad title of", record['title'],Fore.WHITE
						if len(record['description'].split('\n')[0])>2 and not re.match("SONY DSC", record['description']):
								filename=trim(record['description'].split('\n')[0])
						else:
								filename=record['username']
				else:
						filename = record['title']
				for sub in subs:
						filename = re.sub(sub[0], sub[1], filename)
				loop = True
				while len(filename)>200:
						filename = " ".join(filename.split(' ')[:-1])
				if len(filename)<2:
					filename = "SuSanA"
				filename = filename + " ("+ record['id'] + ").jpg"
				
				# Quick check of filename in use - these should be unique
				if nameused(filename.encode('utf-8','ignore')):
						try:
								print Fore.RED, filename.encode('latin-1')
						except:
								print Fore.RED, unidecode(filename)
						print ' Filename found', White
						filenamefound=True
						continue
				else:
						filenamefound=False
						plist=[]
				vc=virinSearch(record['id'])
				if vc==-1:
						print Fore.YELLOW+"Error generating search matches for '"+ record['id'] +"', probably timeout error, skipping file without completing this test",Fore.WHITE
						continue
				if vc>0:
						print Fore.RED+"-"*75
						print Fore.RED+"ID appears to be in use already for", record['id'] +" ("+str(vc)+" matches). Check "+Fore.BLUE+"http://commons.wikimedia.org/w/index.php?search="+ record['id']
						print Fore.RED+"-"*75,Fore.WHITE
						continue
				else:
						#print Fore.GREEN+"No current matches for VIRIN"
						print Fore.BLUE+"http://commons.wikimedia.org/w/index.php?search="+record['id'], Fore.WHITE
						loop=True
				
				d = "== {{int:filedesc}} ==\n{{information"
				if len(record['description'])>1:
						d+= "\n|description={{en|1="+ trim(record['description'])
				else:
						try:
								d+= "\n|description={{en|1=" + record['sets'][0]
						except IndexError:
								d+="\n|description={{Description missing"
				d+= "\n}}"
				d+= "\n|date="+re.sub(" 00:00:00|-00-01", "", record['date'])
				d+= "\n|author=[https://www.flickr.com/people/"+record['nsid']+ " SuSanA Secretariat]"
				d+= "\n|source="+record['url']
				d+= "\n|permission= {{Commons:Batch uploading/Sustainable Sanitation Alliance/credit}}"
				d+= "\n|other_versions="
				other_fields = "\n|other_fields="
				#if record['safety']!='0':
				#		other_fields += "{{Information field|name=Flickr safety level|value=" + ['','Moderate','Restricted'][int(float(record['safety']))] + "}}"
				if record['sets']!=[]:
						other_fields += "{{Information field|name=Flickr sets|value={{flatlist|\n*"+'\n*'.join(record['sets']) + "\n}}}}"
				if record['pools']!=[]:
						other_fields += "{{Information field|name=Flickr pools|value={{flatlist|\n*"+'\n*'.join(record['pools']) + "\n}}}}"
				if record['tags']!=[]:
						other_fields += "{{Information field|name=Flickr tags|value={{flatlist|\n*"+'\n*'.join(record['tags']) + "\n}}}}"
				if len(record['posted'])>1 and not re.search(record['posted'], record['date']):
						other_fields += "{{Information field|name=Flickr posted date|value={{ISOdate|1=" + record['posted'] + "}}}}"
				if len(other_fields)>20:
						d+= other_fields
				d+= "\n}}"
				if len(record['location'])>20:
						d+= '\n'+record['location']
				d+= "\n\n== {{int:license-header}} ==\n"
				d+= record['licence'] + "\n{{Flickrreview}}\n\n"
				for cat in cats:
						keepcat = True
						for ccat in cats:
								if len(cat)< len(ccat):
										if re.search(cat, ccat):
												keepcat = False
						if keepcat:
								d+="\n[[Category:"+cat+"]]"
				d+= "\n[[Category:Files created by Sustainable Sanitation Alliance (SuSanA)]]"
				d+= "\n[[Category:Photos uploaded from Flickr by {{subst:User:Fae/Fae}} using a script]]"
				d+= "\n<!-- Custom upload code: https://github.com/faebug/batchuploads/blob/master/flickr_sanitation.py -->"
				comment = "SuSanA {}, batch reference {}".format(record['id'], count)
				# Check if image is a duplicate on Commons
				source = record['source']
				try:
						duplicate,duptitle = dupcheck(source)
				except Exception, e:
						print Fore.RED+"Error when running the duplicate check '{0}'".format(str(e)), source,Fore.WHITE
						sleep(10)
						try:
								duplicate,duptitle = dupcheck(source)
						except:
								print Fore.RED+"Failed on second try, giving up and skipping"
								continue
				if duplicate:
						print Fore.RED+'File is already on Commons as',duptitle,Fore.WHITE
						sleep(2)
						continue
				lcount=0
				print Fore.GREEN, filename.encode('utf-8'), Fore.WHITE
				while loop:
						try:
								uptry(record['source'],filename,d,comment)
								#print filename
								#print d
								loop=False
								lag=1
								for i in range(lag):
										stdout.write("\r%d " % (lag-i))
										stdout.flush()
										sleep(1)
								stdout.write("\r  ")
								stdout.flush()
								stdout.write("\r")
								uploadcount+=1
								print Fore.GREEN+"Total uploaded:",uploadcount,Fore.YELLOW, time.strftime("%d %b @%H:%M:%S"), Fore.WHITE
						except:
								lcount+=1
								if lcount>3:
										print "Giving up trying to upload after",lcount,"tries"
										loop=False
										remove(localfile)
										continue
								print Fore.RED+"PROBLEM UPLOADING [re-attempt",lcount,"of 3]",time.strftime("%H:%M:%S")+Fore.WHITE
								sleep(5)
