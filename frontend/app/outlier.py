#import requests
import pandas as pd
from pandas import read_sql
import datetime
import matplotlib.pyplot as plt
import numpy as np
import pymysql as mdb
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.svm import OneClassSVM
from sklearn.covariance import EllipticEnvelope

def datetime2str2(t):
    return "%4d%02d%02d"%(t.year,t.month,t.day,)
    
def gen_feat(into):
    unit=6667
    avg=np.average(into)
    if avg==0: avg=1
    chfl=-(into[0]-into[len(into)-1])/avg
    avgdiff=np.average(np.diff(into))/avg
    #diffmm=np.sign(np.argmax(into)-np.argmin(into))*(max(into)-min(into))/avg
    #maxv= np.max(into)/avg
    #minv= np.min(into)
    #rmsv= np.std(into)
    #difxv=np.max(np.diff(into))
    #difnv=np.min(np.diff(into))
    #pop=[avg,maxv]
    #change=[chfl,avgdiff,diffmm]
    #change=[chfl,diffmm]
    #consis=[rmsv/avg,np.std(np.diff(into))]
    #return([avg,avgdiff])
    return([avg,avgdiff])
    #return([avg,diffmm])

def find_outliers(datestart,dateend,plot=False,cut=-0.05):
    numtopics=84

    di=datetime2str2(datestart)
    dfin=datetime2str2(dateend)

    #print di,dfin
    if dfin<di:
        temp=dfin
        dfin=di
        di=temp
    #print di,dfin
    
    afile="/home/ubuntu/mysql_insightwiki_auth.txt"
    a=open(afile)
    passwd=a.readline().rstrip()
    a.close()
    host='localhost'; user='abram.ghost';db='wikidata'
    con = mdb.connect(host, user, passwd, db)#,port=3307)
     
    with con:
        curt= con.cursor()
        #sql="SELECT COUNT(*) FROM `topics` "
        
        sql="SELECT `Id`,`topic_label`,`topic_string` FROM `topics`;"
        curt.execute(sql)
        topics=[[0,'nothing','Filler to match index']]
        for topic in curt:
            topics.append(topic)

    data={}
        
    df=range(numtopics+1)
    with con:
        curt= con.cursor()
        sql="SELECT `Id`,`topic_label`,`topic_string` FROM `topics`;"
        curt.execute(sql)
        for row in curt:
            cur = con.cursor()
            sql='''SELECT `page_views`.`dateonly` AS `vd`, AVG(`page_views`.`count`) AS `vc`, 
                `topics`.`topic_label`,`topics`.`topic_string` 
                FROM `topics` INNER JOIN `page_views` ON `topics`.`ID` = `page_views`.`topic_id` 
                WHERE `topic_id`=%s GROUP BY `page_views`.`dateonly`   '''
            data[row[1]]=read_sql(sql, con,params=[row[0]])
            df[row[0]]=data[row[1]]
    
    topicdata=df
    
    d=topicdata[topics[3][0]]
    p=d[ (d['vd']>di) & (d['vd']<dfin )]['vc'].values    
    topicdata=df
    
    #initializing array to hold the rows to cluster
    #the 0th position is fake so that my index matches the sql index
    clusinp=[]
    clusinp.append(gen_feat([0,0,0,0,0]))
    
    chinaoff=6000
    #populating my array to go into my Kmean
    for index,topic in enumerate(topics):
        #topic=list(topics[index])
        if topic[0]!=0:
            d=topicdata[topic[0]]
            ppre=d[ (d['vd']>di) & (d['vd']<dfin )]['vc'].values
            p=gen_feat(ppre)
            if topic[0]==52:
                p=gen_feat([x-chinaoff if x-chinaoff>=0 else 0 for x in ppre  ])
            clusinp.append(p)
    
    #cleaning up my array making it numpy to go into my kmean
    clusinp=np.array(clusinp)
    clusinp[0]=clusinp[5] #making sure my through away first row matches in size
    #contam=0.325
    contamfix=0.1
    
    colors = ['m', 'g', 'b']
    X1=clusinp
    xx1, yy1 = np.meshgrid(np.linspace(0, 10000, 500), np.linspace(-1.5, 1.5, 500))
    ee=EllipticEnvelope(support_fraction=1., contamination=contamfix)
    #ee=OneClassSVM(nu=contam2, gamma=0.05,kernel='rbf')
    ee.fit(clusinp)
    outliers=ee.decision_function(X1, raw_values=False)
    
    if plot==True:
        print "here"
        get_ipython().magic(u'matplotlib inline')
        Z1 = ee.decision_function(np.c_[xx1.ravel(), yy1.ravel()])    
        Z1 = Z1.reshape(xx1.shape)
        legend1 = plt.contour(xx1, yy1, Z1, levels=[0], linewidths=2, colors=colors[1])
        plt.scatter(X1[:, 0], X1[:, 1], color='black')
        plt.xlim((xx1.min(), xx1.max()))
        plt.ylim((yy1.min(), yy1.max()))
        plt.show()

    out=[]
    for index,outlier in enumerate(outliers):
        row=[index,outlier,topics[index][1],int(np.round(clusinp[index][0])),int(np.round(100*clusinp[index][1]))]
        #row=[index,outlier,topics[index][1],int(np.round(clusinp[index][0])),clusinp[index][1]]
        if outlier<cut and index!=0 and row[3]>8:
            out.append(row)
            #print index,outlier,topics[index][2],clusinp[index][0],clusinp[index][1]
    #out=sorted(out,operator.itemgetter(4))
    #out.sort()
    out=sorted(out,key =lambda x:-x[4])
    return out

#datestart=datetime.datetime(2015,4,17,16)
#dateend=datetime.datetime(2015,4,12,16)
#ol=find_outliers(datestart,dateend,plot=True,cut=0.05)
#for i in ol:
#    print i
 
