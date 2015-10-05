from flask import render_template, request, make_response, send_file
import matplotlib as mpl
mpl.use('Agg')

import re
from app import app
from outlier import find_outliers
import pymysql as mdb
import datetime
#from plot_a_topic import gen_plot

from pandas import read_sql
import seaborn as sns
import matplotlib.pyplot as plt
#import io #StringIO
import StringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
#import operator

def str2date(t):
    out=datetime.datetime.strptime(t, "%m/%d/%Y")
    return out

def str2dateNEW(t):
    year=int(t[-4:])
    month=int(t[:2])
    day=int(t[3:5])
    #print "str2dat",t,year,month,day
    #out=datetime.datetime.strptime(t,"%b/%d/%Y")
    out=datetime.datetime(year,month,day)
    return out

def datefromstr(str):
    return datetime.datetime(int(str[0:4]), int(str[5:7]),int(str[8:]))

def date_parse2(str):
    year =int(str[:4])
    month=int(str[4:6])
    day=int(str[6:8])
    hour=0
    return datetime.datetime(year,month,day,hour)

f=open('/home/ubuntu/mysql_insightwiki_auth.txt')
a=f.readline().rstrip()
f.close()

db = mdb.connect(user="abram.ghost", host="localhost", passwd=a,db="wikidata", charset='utf8')#,port=3307)

@app.route('/')
@app.route('/index')
def index():
    now=datetime.datetime.now()-datetime.timedelta(hours=7)
    dt=datetime.timedelta(days=7)     
    lweek=now-dt
    week="%02d/%02d/%4d"%(lweek.month,lweek.day,lweek.year)
    today="%02d/%02d/%4d"%(now.month,now.day,now.year)
     #print today
    return render_template("index.html",WEEK=week,TODAY=today)

@app.route('/slides')
def slides():
    #return render_template("/plots.png?ID=4")
    return render_template("slides.html")

@app.route('/plots.png')
def plot():
    topicid = request.args.get('ID')
    with db:
        sql='''SELECT `page_views`.`dateonly` AS `vd`, AVG(`page_views`.`count`) AS `vc`, `topics`.`topic_label` AS `tl`,`topics`.`topic_string` 
            FROM `topics` INNER JOIN `page_views` ON `topics`.`ID` = `page_views`.`topic_id` 
            WHERE `topic_id`=%s GROUP BY `page_views`.`dateonly`   '''
        data=read_sql(sql, db,params=[topicid])

    xmin=datetime.datetime(2015,2,1)
    xmax=datetime.datetime(2015,10,1)
    ymin=0;ymax=4000;
    label= data[['tl']].values[0][0]
    data['date']=map(lambda x:date_parse2(x),data['vd'] )
    plt.subplots(figsize=(7,6),)
    fig, ax = plt.subplots(figsize=(7,6),)
    ax.set_xlim([xmin,xmax])
    fig.autofmt_xdate()
    ax.tick_params(axis='both', which='major', labelsize=14)#,colors='Gray')
    sns.despine()
    ax.set_title(label, fontsize=20)
    #ax.title.set_color('Gray')
    ax.plot_date(data[['date']].values,data[['vc']].values,'.',ms=15,alpha=0.9)
    ax.set_ylabel('Wikipedia Page Views', fontsize=14)
    #ax.yaxis.label.set_color('Gray')
    canvas = FigureCanvas(fig)
    #output = io.BytesIO  #StringIO.StringIO()
    output = StringIO.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/plots')
def plots():
  topicid = request.args.get('ID')
  return render_template("plots.html",ID=topicid )

@app.route('/home')
def home():
  err=""
  datestart = request.args.get('SDATE')
  dateend = request.args.get('EDATE')
 
  now=datetime.datetime.now()
  try: 
    datestart=datetime.datetime.strptime(datestart, "%m/%d/%Y")
  except ValueError:
    datestart=datetime.datetime.now()-datetime.timedelta(days=+7)
    err="Start date was not in the correct format"
 
  try: 
    dateend=datetime.datetime.strptime(dateend, "%m/%d/%Y")
  except ValueError:
    dateend=now
    err="End date was not in the correct format"

  dt=datetime.timedelta(days=+0)     
  mindt=datetime.timedelta(hours=48)     
  dt=datetime.timedelta(hours=24)     
  while datestart<=dateend and datestart+mindt>=dateend:
    dateend=dateend+dt
    err="The requested time slice was shorter than 3 days which is to small to take a difference"

  jan=datetime.datetime(2015,01,01)
  if datestart<jan:
     datestart=jan
     err="Start date was not in the considered time window (01/2015-Present)"
  if dateend<jan:
     dateend=jan+datetime.timedelta(days=+7) 
     err="End date was not in the considered time window (01/2015-Present)"
  if datestart>now:
     datestart=datetime.datetime(now.year,now.month,now.day)-datetime.timedelta(days=+7)
     err="Start date was not in the considered time window (01/2015-Present)"
  if dateend>now:
     dateend=datetime.datetime(now.year,now.month,now.day)
     err="End date was not in the considered time window (01/2015-Present)"

  outliers=find_outliers(datestart,dateend)
  fortab=[]
 
  now=datetime.datetime.now()-datetime.timedelta(hours=7)
  dt=datetime.timedelta(days=7)     
  lweek=now-dt
  week="%02d/%02d/%4d"%(lweek.month,lweek.day,lweek.year)
  today="%02d/%02d/%4d"%(now.month,now.day,now.year)
  #print today
  for result in outliers:
    fortab.append(dict(Id=result[0], mdist=result[1], lab=result[2],pviews=result[3],change=result[4]))
  return render_template("home.html", fortab=fortab,datestart=datestart.date(), dateend=dateend.date(),WEEK=week,TODAY=today,ERROR=err)

