from flask import render_template, request
from cluster import get_selected
from app import app
import pymysql as mdb
import datetime

f=open('/Users/abramvandergeest/mysql_insightwiki_auth.txt')
a=f.readline().rstrip()
f.close()

db = mdb.connect(user="abram.ghost", host="localhost", passwd=a,db="wikidata", charset='utf8',port=3307)

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
        title = 'Home',
        user = { 'nickname': 'Miguel' })

@app.route('/input')
def topics_input():
   return render_template("input.html")

@app.route('/output')
def topics_output():
 #pull 'ID' from input field and store it
  topic = request.args.get('ID')
  date = request.args.get('DATE')
  print topic, date
  if date=="": 
      date=datetime.datetime(2015,8,15,16)
  else:
      date=datetime.datetime(int(date[:4]),int(date[4:6]),int(date[6:8]))

  with db:
    cur = db.cursor()
    cur.execute("SELECT `Id`,`topic_label`,`topic_string` FROM `topics` WHERE `topic_string` LIKE %s;" , ("%%%s%%" % topic,) )
    query_results = cur.fetchall()

  pageviews=-1  
  if len(query_results)>0:
      print query_results[0]
      out=get_selected(query_results[0][0],date,6,True)
      pageviews=out[1]
      print out[0]
      print out[1],"!!!!!!!!"

  thresh=800. #Ultimately I can make an adaptive threshold
  if pageviews==-1:
    print "no results"
    pvstr="The topic %s is not considered in this study."%(topic)
  elif pageviews>=thresh:
     pvstr="%s is relavent for %s with popularity of %f"%(query_results[0][2].title(),date,pageviews/thresh )   
  elif pageviews>=0 and pageviews<thresh:
     pvstr="%s is NOT relavent for %s with popularity of %f"%(query_results[0][2].title(),date,pageviews/thresh )   

  topics=[[1,2,3,4,5]]
  if pageviews >0:
    print out[0][0]
    topics = []
    for result in out[0]:
      topics.append(dict(Id=result[0], toplab=result[1], topstr=result[2]))
  
  the_result = 5 #pop_input #ModelIt(city, pop_input)
  return render_template("output.html", cities = topics, the_result = the_result, date=date,pvstr=pvstr)
