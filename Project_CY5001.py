

from collections import Counter, defaultdict
import operator
import argparse
import os

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
import base64
from datetime import datetime
import socket
import shutil

try: 
    from scapy.all import *
except:
    print("ERROR: Sorry, could not import scapy. Try 'pip3 install scapy-python3'.")
    quit()

try: 
    from prettytable import PrettyTable
except:
    print("ERROR: Sorry, could not import prettytable. Try 'pip3 install prettytable'.")
    quit()


parser = argparse.ArgumentParser(description='PCAP File Examiner')
parser.add_argument('file', help="Source PCAP File, i.e. example.pcap", type=str)
parser.add_argument('--flows', help="Display flow summary", action="store_true")
parser.add_argument('--dst', help="Display count of destination IPs", action="store_true")
parser.add_argument('--src', help="Display count of source IPs", action="store_true")
parser.add_argument('--dport', help="Display count of destination ports", action="store_true")
parser.add_argument('--sport', help="Display count of source ports", action="store_true")
parser.add_argument('--ports', help="Display count of all ports", action="store_true")
parser.add_argument('--portbytes', help="Display ports by bytes", action="store_true")
parser.add_argument('--bytes', help="Display source and destination byte counts", action="store_true")
parser.add_argument('--dns', help="Display all DNS Lookups in PCAP", action="store_true")
parser.add_argument('--url', help="Display all ULRs in PCAP", action="store_true")
parser.add_argument('--netmap', help="Display a network Map", action="store_true")
parser.add_argument('--xfiles', help="Extract files from PCAP", action="store_true")
parser.add_argument('--resolve', help="Resolve IPs", action="store_true")
parser.add_argument('--details', help="Display aditional details where available", action="store_true")
parser.add_argument('--graphs', help="Display graphs where available", action="store_true")
parser.add_argument('--timeseries', help="Display data over time", action="store_true")
parser.add_argument('--all', help="Display all", action="store_true")
parser.add_argument('--limit', help="Limit results to X", type=int)
parser.add_argument('--skipopts', help="Don't display the options at runtime", action="store_true")
parser.add_argument('--outdir', help="Output directory for files, default = pwd ", action="store")
args=parser.parse_args()

if args.all:
    args.dst=True
    args.flows=True
    args.bytes=True
    args.dst=True
    args.src=True
    args.portbytes=True
    args.dns=True
    args.url=True
    args.xfiles=True
    args.graphs=True
    args.details=True
    args.timeseries=True

if args.url or args.xfiles or args.all:
    try:
        from scapy_http import http
        import ipaddress
    except:
        print("""ERROR: Scapy does not have http support, skipping url mining.
        You can try the following: 
            wget https://github.com/invernizzi/scapy-http/archive/master.zip
            unzip master.zip
            cd scapy-http-master
            sudo python3 ./setup.py build install. """)
        args.url=False

if args.graphs:
    try:
        import plotly
        import plotly.graph_objs as go
    except:
        print("ERROR: Plotly not installed, try pip3 install plotly") 
        quit()

if args.netmap:
    try:
        import networkx as nx
    except:
        print("ERROR: NetworkX not installed, try pip3 install networkx")
        quit()
if args.timeseries:
    try:
        import pandas as pd
    except:
        print("ERROR: Pandas not installed, try pip3 install pandas")
        quit()

if args.outdir:
    #check to see if output file exists
    if not os.path.isdir(args.outdir):
        try:
            os.mkdir(args.outdir)
        except:
            print('ERROR: Unable to create output directory ' + args.outdir)
            quit()



if os.path.isfile(args.file):
    print("--Reading pcap file")
    try:
        pkts = rdpcap(args.file)
    except:
        print("ERROR: Unable to open the pcap file {}, check  permissions".format(args.file))
else: 
    print("ERROR: Can't open pcap file {}".format(args.file))
    quit()

srcIP=[]
dstIP=[]
srcdst=[]
sport=[]
dport=[]
port=[]
i=0
for pkt in pkts:
    if IP in pkt:
        try:
            srcIP.append(pkt[IP].src)
            dstIP.append(pkt[IP].dst)
            srcdst.append(pkt[IP].src + ","  + pkt[IP].dst)
            dport.append((pkt[IP].dport))
            sport.append((pkt[IP].sport))
            port.append((pkt[IP].sport))
            port.append((pkt[IP].dport))
        except:
            pass

def resolveName(addr):
    try:
        addrList=socket.gethostbyaddr(addr)
        addr=addrList[0]
    except:
        pass
    return addr

def simpleCount(ipList, limit, headerOne, headerTwo, title):
    table= PrettyTable([headerOne, headerTwo])
    cnt = Counter()
    yData=[]
    xData=[]
    for ip in ipList:
        cnt[ip] += 1
    i=0
    for item, count in cnt.most_common(): 
        item=str(item)
        if args.resolve:
            table.add_row([formatCell(resolveName(item)),count])
        else:
            table.add_row([formatCell(item),count])
        yData.append(count)
        xData.append(item)

        if limit:
            if i >= limit:
                break
        i+=1
    print(title)
    print(table)	
    if args.graphs: 
        createGraph(xData, yData, headerOne, headerTwo, title)

def makeFilename(title):
    title=title.replace(" ","-")
    title=title.replace("/","")
    if args.outdir:
        title=args.outdir + "/" + title

    return title + ".html"
    
def createGraph(xData, yData, xTitle, yTitle, title): 
    plotly.offline.plot({ 
        "data":[ go.Bar( x=xData, y=yData) ], 
        "layout": go.Layout(title=title, 
            xaxis=dict(title=xTitle),
            yaxis=dict(title=yTitle))
        },filename=makeFilename(title))


def createPieGraph(xData, yData, xTitle, yTitle, title): 
    pie={'data': [ {'labels' : xData, 
            'values': yData,
            'type' : 'pie' }],
            "layout": { 'title' }
            }
    plotly.offline.plot(pie, filename=makeFilename(title))

def simpleCountDetails(itemList, itemDict, limit, headerOne, headerTwo, headerThree, title):
    yData=[]
    xData=[]
    table=PrettyTable([headerOne, headerTwo, headerThree])
    cnt = Counter()
    for item in itemList:
        cnt[item] += 1
    i=0
    for item, count in cnt.most_common():
        yData.append(count)
        xData.append(item)
        items=""
        j=0
        for x in itemDict[item]: 
            if j < len(itemDict[item]):
                items += x + "\n"
            else: 
                items += x
            j+=1
        if args.resolve:
            table.add_row([formatCell(resolveName(item)),count,itemDict[item]])
        else:
            table.add_row([formatCell(item),count,items])
        if limit:
            if i >= limit:
                break
        i+=1

    print(title)
    print(table)
    if args.graphs:
        createGraph(xData, yData, headerOne, headerTwo, title)

def formatCell(x):
    termWidth=shutil.get_terminal_size().columns
    colWidth= (termWidth // 3)  * 2 
    chunks=""
    if len(x) > colWidth:
        for chunk in [x[i:i+colWidth] for i in range(0, len(x), colWidth)]:
            if len(chunk) == colWidth:
                chunks += chunk + "\n"
            else:
                chunks += chunk
        return chunks
    else:
        return x

def flowCount(ipList, limit):
    table= PrettyTable(["Src", "Dst", "Count"])
    cnt = Counter()
    yData=[]
    xData=[]
    for ip in ipList:
        cnt[ip] += 1
    i=0
    for item, count in cnt.most_common(): 
        yData.append(count)
        xData.append(item)
        src,dst=item.split(',')
        if args.resolve:
            table.add_row([resolveName(src),resolveName(dst), count])
        else:
            table.add_row([src, dst, count])
        if limit:
            if i >= limit:
                break
        i+=1

    print("Src IP/Dst IP Counts")
    print(table)	
    if args.graphs:
        createGraph(xData, yData, "IPs", "Count", "Flows")


def byteCount(pkts, srcdst, limit):
    yData=[]
    xData=[]
    srcdstbytes={}
    table= PrettyTable(["Src", "Dst", "Bytes"])
    for pkt in pkts:
        if IP in pkt:
            srcdst=pkt[IP].src + ","  + pkt[IP].dst
            if srcdst in srcdstbytes:
                newBytes=srcdstbytes[srcdst] + pkt[IP].len
                srcdstbytes[srcdst] = newBytes 
            else:
                srcdstbytes[srcdst] = pkt[IP].len
    i=0
    for srcdst, bytes in sorted(srcdstbytes.items(), key=operator.itemgetter(1), reverse=True):
        yData.append(bytes)
        xData.append(srcdst)
        src,dst=srcdst.split(',')
        if args.resolve:
            table.add_row([resolveName(src),resolveName(dst), bytes])
        else:
            table.add_row([src, dst, bytes])
        if limit:
            if i >= limit:
                break
        i+=1

    print(table)
    if args.graphs:
        createGraph(xData, yData, "IPs", "Bytes", "Src/Dst Byte Count")

def portBytes(pkts, limit):
    yData=[]
    xData=[]
    portBytes={}
    table= PrettyTable(["Port", "Bytes"])
    for pkt in pkts:
        if IP in pkt:
            try: 
                sport=pkt[IP].sport
                if sport in portBytes:
                    newBytes=portBytes[sport] + pkt[IP].len
                    portBytes[sport] = newBytes 
                else:
                    portBytes[sport] = pkt[IP].len
            except:
                pass
    i=0
    for sport, bytes in sorted(portBytes.items(), key=operator.itemgetter(1), reverse=True):
        yData.append(bytes)
        xData.append(sport)
        table.add_row([sport, bytes])
        if limit:
            if i >= limit:
                break
        i+=1

    print(table)
    if args.graphs:
        createPieGraph(xData, yData, "Ports", "Bytes", "Traffic by Port and Bytes")

def dnsCount(pkts, limit, headerOne, headerTwo, title):
    lookups=[]
    queryClients={}
    for pkt in pkts:
        if IP in pkt:
            if pkt.haslayer(DNS) and pkt.getlayer(DNS).qr == 0:
                lookup=(pkt.getlayer(DNS).qd.qname).decode("utf-8")
                if args.details:
                    if lookup in queryClients:
                        if pkt[IP].src not in queryClients[lookup]:
                            queryClients[lookup].append(pkt[IP].src)
                    else:
                        queryClients[lookup] = [pkt[IP].src]

                if "arpa" not in lookup:
                    lookups.append(lookup)
     
    if args.details:
        simpleCountDetails(lookups, queryClients, limit, headerOne, headerTwo, 'Clients', title)
    else:
        simpleCount(lookups, limit, headerOne, headerTwo, title)



def urlCount(pkts, limit, headerOne, headerTwo, title):
    urls=[]
    urlClients={}
    for pkt in pkts:
        if IP in pkt:
            if http.HTTPRequest in pkt:
                uri=(pkt[http.HTTPRequest].Path).decode("utf-8")
                host=(pkt[http.HTTPRequest].Host).decode("utf-8")
                if args.resolve:
                    try:
                        ipaddress.ip_address(host)
                        host=resolveName(host) 
                    except:
                        pass
                url=host+uri
                urls.append(url)
                if args.details:
                    if url in urlClients:
                        if pkt[IP].src not in urlClients[url]:
                            urlClients[url].append(pkt[IP].src)
                    else:
                        urlClients[url]=[pkt[IP].src]
    if args.details:
        simpleCountDetails(urls, urlClients, limit, headerOne, headerTwo, 'Clients', title)
    else:
        simpleCount(urls, limit, headerOne, headerTwo, title)




def extractFiles(pkts):
    print("--Creating output in ./pxOutput")
    if not os.path.exists('pxOutput'):
        os.mkdir('pxOutput')
    else:
        print('---Dir exists, skipping creation of pxOutput directory')

    for pkt in pkts:
        if pkt.haslayer(TCP) and (pkt.dport == 80 or pkt.sport == 80 ):
            if http.HTTPResponse in pkt:
                contentType=getattr(pkt[http.HTTPResponse], 'Content-Type', None)
                if contentType != None:
                    contentType=contentType.decode("utf-8")
                    if "text" in contentType or "javascript" in contentType:
                        try:
                            pktContent=((pkt[http.HTTPResponse].load).decode("utf-8"))   
                            writePktFile(pkt, contentType, pktContent)
                        except:
                            pass
                        try:    
                            pktContent=(str(base64.b64decode(pkt[http.HTTPResponse].load).decode("utf-8")))
                            writePktFile(pkt, contentType, pktContent)
                        except:
                            pass
                    if "image" in contentType:
                        try:
                            pktContent=(pkt[http.HTTPResponse].load)
                            writePktFile(pkt, contentType, pktContent)
                        except:
                            pass

def writePktFile(pkt, contentType, pktContent):
    try:
        pktDate=(pkt[http.HTTPResponse].Date).decode("utf-8")
        pktDate=datetime.strptime(pktDate, '%a, %d %b %Y %H:%M:%S %Z')
        pktDate=pktDate.strftime('%Y-%m-%d::%H:%M:%S')
    except:
        pktDate='1970-01-01::01:01:01'

    if 'javascript' in contentType:
        extension='.js'
        wt='w'
    elif 'html' in contentType:
        extension='.html'
        wt='w'
    elif 'jpeg' in contentType:
        extension = '.jpg'
        wt='wb'
    elif 'png' in contentType:
        extension = '.png'
        wt='wb'
    elif 'gif' in contentType:
        extension = '.gif'
        wt='wb'

    pktFile="pxOutput/" + pktDate + extension
    print("---Creating file {} ".format(pktFile))
    fh=open(pktFile, wt)
    fh.write(pktContent)
    fh.close()

def timeSeries(pkts, title, xTitle, yTitle):
    pktBytes=[]
    pktTimes=[]
    for pkt in pkts:
        if IP in pkt: 
            try:
                pktBytes.append(pkt[IP].len)
                pktTime=datetime.fromtimestamp(pkt.time)
                pktTimes.append(pktTime.strftime("%Y-%m-%d %H:%M:%S.%f"))
            except:
                pass

    bytes = pd.Series(pktBytes).astype(int)
    times = pd.to_datetime(pd.Series(pktTimes).astype(str),  errors='coerce')
    df  = pd.DataFrame({"Bytes": bytes, "Times":times})
    df = df.set_index('Times')
    df2=df.resample('2S').sum()

    table= PrettyTable(["Time", "Bytes"])
    for row in df2.iterrows():
        table.add_row([row[0], row[1]['Bytes']])
    print(table)

    if args.graphs:
        plotly.offline.plot({
            "data":[plotly.graph_objs.Scatter(x=df2.index, y=df2['Bytes'])],
            "layout":plotly.graph_objs.Layout(title=title, xaxis=dict(title=xTitle), yaxis=dict(title=yTitle))}, filename=makeFilename(title))

if args.src:
    simpleCount(srcIP, args.limit, "Source IP", "Count", "Source IP Occurence")
if args.dst:
    simpleCount(dstIP, args.limit, "Dest IP", "Count", "Dest IP Occurence")
if args.dport: 
    simpleCount(dport, args.limit, "Dest Port", "Count", "Dest Port Occurence")
if args.sport: 
    simpleCount(sport, args.limit, "Source Port", "Count", "Source Port Occurence")
if args.ports: 
    simpleCount(port, args.limit, "Port", "Count", "Port Occurence")
if args.flows:
    flowCount(srcdst, args.limit)
if args.bytes:
    byteCount(pkts, srcdst, args.limit)
if args.dns:
    dnsCount(pkts, args.limit, "DNS Lookup", "Count", "Unique DNS Lookups")
if args.url:
    urlCount(pkts, args.limit, "URL", "Count", "Unique URLs" )
if args.xfiles:
    extractFiles(pkts)
if args.portbytes:
    portBytes(pkts, args.limit)
if args.timeseries:
    timeSeries(pkts, "Traffic over Time", "Date", "Bytes" )
