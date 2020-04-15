import urllib
from urllib.request import urlopen
import urllib.request
import string
import sys
from bs4 import BeautifulSoup
import sqlite3
from datetime import date
import codecs
import json
import datetime

conn = sqlite3.connect('Rotten.sqlite')
c = conn.cursor()
c2 = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS Rotten('id' INTEGER, 'Title' VARCHAR, 'Critic' TEXT, 'Audience' TEXT, 'dvdrelease' DATETIME, 'Seen' Text, 'trending' BOOL,'url' TEXT  )")

rows = c.execute("Update Rotten Set trending=0 ")

baseurl = "https://www.rottentomatoes.com/api/private/v2.0/browse?maxTomato=100&services=amazon%3Bhbo_go%3Bitunes%3Bnetflix_iw%3Bvudu%3Bamazon_prime%3Bfandango_now&certified=false&sortBy=popularity&type=top-dvd-streaming&page="
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0'
headers = { 'User-Agent' : user_agent }

currentpage =1
totalpages = 1
trendingPosition = 1

while currentpage <= totalpages:
    request=urllib.request.Request(baseurl+str(currentpage)  ,None ,headers)
    response = urlopen(request)
    the_page = response.read()
    RT= json.loads(the_page)

    today = date.today().strftime("%m/%d/%Y")

    for movie in RT['results']:
        title = movie['title']
        movieid = movie['id']
        url= movie['url']

        #TODO deal with year rollover
        dvdrelease= datetime.datetime.strptime(movie['dvdReleaseDate']+" "+str(date.today().year),"%b %d %Y")
        daysreleased = datetime.datetime.now() - dvdrelease
        if daysreleased.days < -180:
            dvdrelease = dvdrelease - datetime.timedelta(days=365)
        

        
        dvdreleasedate = dvdrelease.strftime("%Y-%m-%d")


        rows  = c.execute("SELECT EXISTS( SELECT * from Rotten Where id = '" + str(movieid) +"')" )
        if rows.fetchone()[0] == 0:
            print("Inserting "+title)
            c.execute("Insert into Rotten (id, Title, dvdrelease, trending, url ) Values (?,?,?,?,?) ",(movieid,title,dvdreleasedate,str(trendingPosition),url) )
        else:
            c.execute("Update Rotten set trending="+str(trendingPosition)+" where id ='" +str(movieid) +"'")

        trendingPosition +=1

    if currentpage ==1:
        totalpages= int(RT['counts']['total']/RT['counts']['count']) +1

        
    currentpage +=1
    
rows= c2.execute("SELECT id, url from Rotten where trending > 0 and Critic is Null")
for row in rows:
    print(row[1])
    request=urllib.request.Request("https://www.rottentomatoes.com"+row[1],None ,headers)           
    response = urlopen(request)
    the_page = response.read()    
    jsonrow  = the_page.find(b"root.RottenTomatoes.context.scoreInfo")
    jsonstart = the_page.find(b"{",jsonrow)
    jsonend = the_page.find(b";",jsonstart)
    jsondata= the_page[jsonstart: jsonend]
    RT2 = json.loads(jsondata.decode())

    critics = ""
    audience = ""

    try:
        critics = str(RT2['tomatometerAllCritics']['score'])
    except:
        pass

    try:
        audience = str(RT2['audienceAll']['score'])
    except:
        pass

    c.execute("Update Rotten set Critic= '"+critics+"', Audience ='"+audience+ "' Where id='"+str(row[0])+"'")


    print(str(row[0])+" "+row[1]+" Critic: "+critics+" Audience: "+audience)


rows = c.execute("SELECT Title, Critic, Audience, trending "
                 +"FROM Rotten "
                 +"WHERE seen is null AND trending>=1 "
                 +"ORDER BY cast(trending as int) ASC")

print(str.ljust("#",4)+str.ljust("MOVIE",50)+str.ljust("CRITIC",10)+str.ljust("AUDIENCE",10))

for row in rows:        
    print(str(row[3]).ljust(3)+row[0].ljust(50)+row[1].ljust(10)+row[2].ljust(10))


conn.commit()
conn.close()
