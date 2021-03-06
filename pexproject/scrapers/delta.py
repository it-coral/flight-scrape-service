#!/usr/bin/env p
import sys
import datetime
import time
import re
import json
import urllib
import codecs
from datetime import timedelta
from bs4 import BeautifulSoup
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEV_LOCAL = False

if not DEV_LOCAL:
    import customfunction
else:
    import pdb

def delta(orgn, dest, searchdate, searchkey):
    if not DEV_LOCAL:
        db = customfunction.dbconnection()
        cursor = db.cursor()
        db.set_character_set('utf8')
    url = "http://www.delta.com/"   
    searchid = str(searchkey)
    currentdatetime = datetime.datetime.now()
    stime = currentdatetime.strftime('%Y-%m-%d %H:%M:%S')
    sys.stdout=codecs.getwriter('utf-8')(sys.stdout)

    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true',
                                               '--ssl-protocol=any',
                                               '--load-images=false'],
                                 service_log_path='/tmp/ghostdriver.log')

    driver.set_window_size(1120, 1080)  
    # driver = webdriver.Firefox()

    def storeFlag(searchkey,stime):
        if not DEV_LOCAL:
            cursor.execute ("INSERT INTO pexproject_flightdata (flighno,searchkeyid,scrapetime,stoppage,stoppage_station,origin,destination,duration,maincabin,maintax,firstclass,firsttax,business,businesstax,cabintype1,cabintype2,cabintype3,datasource,departdetails,arivedetails,planedetails,operatedby,economy_code,business_code,first_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", ("flag", str(searchkey), stime, "flag", "test", "flag", "flag","flag", "0","0", "0","0", "0", "0", "flag", "flag", "flag", "delta", "flag", "flag", "flag", "flag", "flag", "flag", "flag"))
            db.commit()
        driver.quit()
    try:
        driver.get(url)
        time.sleep(1)
        flg = 0
        pageStatus = ''
        while flg < 15 and pageStatus != 'complete':
            time.sleep(1)
            print "flg",flg
            pageStatus = driver.execute_script('return document.readyState;')
            print "pageStatus",pageStatus
            flg = flg+1
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.ID, "oneWayBtn")))
        oneway = driver.find_element_by_id('oneWayBtn')
        #oneway.click()
        driver.execute_script("arguments[0].click();", oneway)
        driver.execute_script("document.getElementById('originCity').setAttribute('value', '"+orgn.strip()+"')")
        # origin = driver.find_element_by_id("originCity")
        # origin.clear()
        # origin.send_keys(orgn.strip())
        driver.execute_script("document.getElementById('destinationCity').setAttribute('value', '"+dest.strip()+"')")
        # destination = driver.find_element_by_id("destinationCity")
        # destination.send_keys(dest.strip())
        ddate = driver.find_element_by_id("departureDate")  
        driver.execute_script("document.getElementById('departureDate').setAttribute('value', '"+str(searchdate)+"')")
        milebtn = driver.find_element_by_id("milesBtn")
        milebtn.click()
        driver.find_element_by_id("findFlightsSubmit").send_keys(Keys.ENTER)
        
    except:
        print "before data page"
        storeFlag(searchkey,stime)
        return searchkey
    time.sleep(1)
    try:
        WebDriverWait(driver,5).until(EC.presence_of_element_located((By.ID, "submitAdvanced")))
        print "no data"
        storeFlag(searchkey,stime)
        return searchkey
    except:
        print "Data found"
    try:
        # driver.save_screenshot('/root/out_enter.png');
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "showAll-footer")))
        print "More than one page"
        driver.execute_script("""
            DWRHandler.currentPage = -1;
            var _shopInputDo=shopInputDo;
            shoppingUtil.scrollWindow("top");
            FilterFunctions.showFilterMsg();
            FlightUtil.emptyResults();
            ResummarizeFlightResultsDWR.pageResults(DWRHandler.currentPage, _shopInputDo.currentSessionCheckSum, delta.airShopping.cacheKey, {
            async: true,
            callback: function(searchResults) {
                if (searchResults != null) {
                    var jsonData = {};
                    jsonData['jsonobj'] = JSON.stringify(searchResults);
                    var cabininfo = document.getElementsByClassName('tblHeadUp')[0].innerHTML;
                    jsonData['cabinTypes'] = cabininfo;
                    localStorage.setItem('deltaData', JSON.stringify(jsonData));
                    var element = document.createElement('div');
                    element.id = "submitAdvanced";
                    element.appendChild(document.createTextNode("text"));
                    document.body.appendChild(element);
                    throw new Error("Results found");
                    if (searchResults.errorFwdURL == null) {
                        jsonResultPopulation(searchResults);
                        paginationPopulation(searchResults);
                        if (shoppingUtil.isIE8()) {
                            if (DWRHandler.currentPage == -1) {
                                ieTimeout = setTimeout("RenderTemplate.renderResult();FilterFunctions.hideFilterMsg();RenderTemplate.adjustHeight();", 200);
                            } else {
                                ieTimeout = setTimeout("RenderTemplate.renderResult();FilterFunctions.hideFilterMsg();RenderTemplate.adjustHeight();", 100);
                            }
                        } else {
                            RenderTemplate.renderResult();
                            FilterFunctions.hideFilterMsg();
                            RenderTemplate.adjustHeight();
                        }
                        if (DWRHandler.currentPage == -1) {
                            $("#showAll").hide();
                            $("#showAll-footer").hide();
                        }
                        contienuedOnload(false);
                        if (searchResults.debugInfo != null && ((typeof(printRequestResponse) !== "undefined") && printRequestResponse == true)) {
                            $("#requestXml").text(searchResults.debugInfo.itaRequest);
                            $("#responceXml").text(searchResults.debugInfo.itaResponse);
                            $("#reqRes").show();
                        }
                    } else {
                        window.location.replace(searchResults.errorFwdURL);
                    }
                } else {
                    FilterFunctions.errorHandling();
                }
                $(".tableHeaderHolderFareBottom.return2Top").show();
            },
            exceptionHandler: FilterFunctions.errorHandling
        });
        """)
    except:
        print "single page"
        try:
            driver.execute_script("""
            var sortBy = "deltaScheduleAward" ;
            SearchFlightResultsDWR.searchResults(currentSessionCheckSum, sortBy[0], delta.airShopping.numberOfColumnsToRequest, delta.airShopping.cacheKey, {
                async: true,
                timeout: 65000,
                callback: function(searchResults) {
                        var jsonData = {};
                        
                        jsonData['jsonobj'] = JSON.stringify(searchResults);
                        var cabininfo = document.getElementsByClassName('tblHeadUp')[0].innerHTML;
                        jsonData['cabinTypes'] = cabininfo;
                        localStorage.setItem('deltaData', JSON.stringify(jsonData));
                        var element = document.createElement('div');
                        element.id = "submitAdvanced";
                        element.appendChild(document.createTextNode("text"));
                        document.body.appendChild(element);
                        throw new Error("Results found");
                        
                    if (searchResults.errorFwdURL == null || searchResults.errorFwdURL == "") {
                        flightResultsObj.isDOMReady(searchResults, action, false);
                        FilterFunctions.hideFilterMsg();
                    } else {
                    
                        flightResultsObj.isDOMReady(searchResults, false, true);
                    }
                    if (!action) {
                        Wait.hide();
                        $(".tableHeaderHolderFareBottom").show();
                        $("#nextGenAirShopping .tableHeaderHolder").show();
                    }
                },
                errorHandler: function(msg, exc) {
                    shoppingUtil.errorHandler(msg, exc);
                },
                exceptionHandler: function(msg, exc) {
                    (action) ? FilterFunctions.hideFilterMsg(): "";
                    shoppingUtil.exceptionHandler(msg, exc);
                }
            });
            
            """)
        except:
            storeFlag(searchkey,stime)
            return searchkey
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "submitAdvanced")))
        result = driver.execute_script(""" return localStorage.getItem('deltaData'); """)
        deltaObj = json.loads(result)
        a_file = open('1.json', 'w')
        a_file.write(json.dumps(deltaObj, indent=4))
        # a_file.write(result.encode('utf8'))
        # print deltaObj, '@@@@@@'
        # return
        searchResult = json.loads(deltaObj['jsonobj'])
        # a_file = open('2.json', 'w')
        # a_file.write(json.dumps(searchResult, indent=4))
        # return

        cabinhead = "<tr>"+deltaObj['cabinTypes']+"</tr>"
        soup = BeautifulSoup(cabinhead,"xml")
        tds = soup.findAll("td")
        pricecol = ''
        pricecol =  soup.findAll("a",{"class":"tblHeadBigtext lnkCabinName"})
        if len(pricecol) < 1:
            pricecol = soup.findAll("label",{"class":"tblHeadBigtext"})
        flightData = searchResult["itineraries"]
    except:
        # raise
        storeFlag(searchkey,stime)
        return searchkey
    
    values_string = []
    for i in range(0,len(flightData)):
        totalFareDetails = flightData[i]['totalFare']
        slicesDetails = flightData[i]['slices']
        departDetail = []
        ariveDetail = []
        flightDetail = []
        operatorDetail = []
        SourceCOde =''
        tripDuration=''
        destinationCode=''
        arivalTime=''
        departTime=''
        flightNo = ''
        for k in range(0,len(slicesDetails)):
            tripDuration = slicesDetails[k]['duration']
            SourceCOde = slicesDetails[k]['sliceOrigin']['airportCode']
            destinationCode = slicesDetails[k]['sliceDestination']['airportCode']
            arivalTime = slicesDetails[k]['sliceArrivalTime']
            departTime = slicesDetails[k]['sliceDepartureTime']
            layover = slicesDetails[k]['flights']
            "**************************************** FLIGHT DETAILS ****************************************"
            FlightFlag = 0
            for m in range(0,len(layover)):
                legData = layover[m]['legs']
                for n in range(0,len(legData)):
                    legdetail = legData[n]
                    if legdetail:
                        fromAirport =''
                        destAirport=''
                        "=========================LEG INFO=================================="
                        if 'origin' in legdetail:
                            orgnCode = legdetail['origin']['airportCode']
                            cityname = legdetail['origin']['nearByCities'][0]['name']
                            cityCode = legdetail['origin']['nearByCities'][0]['country']['region']['code']
                            fromAirport = orgnCode
                             
                        if 'destination' in legdetail:
                            destCode = legdetail['destination']['airportCode']
                            destcityname = legdetail['destination']['nearByCities'][0]['name']
                            destcityCode = legdetail['destination']['nearByCities'][0]['country']['region']['code']
                            destAirport = destCode
                        
                        duration = legdetail['duration']
                        schedDepartureTime = legdetail['schedDepartureTime']
                        schedDepartureDate = legdetail['schedDepartureDate']
                        schedArrivalTime = legdetail['schedArrivalTime']
                        schedArrivalDate = legdetail['schedArrivalDate']

                        '@@@@@@@ departDetails format @@@@@@@'
                        departinfo_time = schedDepartureDate+" "+schedDepartureTime
                        departinfo_time = datetime.datetime.strptime(departinfo_time, '%a %b %d %Y %I:%M%p')
                        departinfo_time = departinfo_time.strftime('%Y/%m/%d %H:%M')

                        if not DEV_LOCAL:
                            fromAirport = customfunction.get_airport_detail(fromAirport) or fromAirport
                        fromDetail = departinfo_time+" | from  "+fromAirport
                        departDetail.append(fromDetail)
                        departinfo_time = schedArrivalDate+" "+schedArrivalTime
                        departinfo_time = datetime.datetime.strptime(departinfo_time, '%a %b %d %Y %I:%M%p')
                        departinfo_time = departinfo_time.strftime('%Y/%m/%d %H:%M')

                        if not DEV_LOCAL:
                            destAirport = customfunction.get_airport_detail(destAirport) or destAirport
                        toDetails = departinfo_time+" | at "+destAirport
                        ariveDetail.append(toDetails)
                        aircraft = legdetail['aircraft']['shortName']
                        airlineCode = legdetail['marketAirline']['airline']['airlineCode']
                        flightNumber = legdetail['flightNumber']
                        if FlightFlag == 0:
                            flightNo = airlineCode+" "+str(flightNumber)

                        # --- NORM ---
                        if aircraft[:3] == 'MD-':
                            aircraft = 'McDonnell Douglas MD ' + aircraft[3:]
                        elif aircraft[:3] == 'CRJ':
                            aircraft = 'Bombardier ' + aircraft
                        flightFormat = airlineCode+" "+str(flightNumber)+" | "+aircraft+" ("+duration+")"
                        flightDetail.append(flightFormat)
                        operatedby = legdetail['operatingAirline']['airline']['airlineName']
                        operatorDetail.append(operatedby)
                        FlightFlag = FlightFlag+1
        "====================Fare info ================================="
      
        fareFlag = 0
        cabintype1 =''
        cabintype2 = ''
        cabintype3 = ''
        ecofare = 0
        echoTax = 0
        bussfare = 0
        busstax = 0
        firstFare =0
        firsttax =0
        ecofareClass = ''
        bussFareClass = ''
        firstFareClass = ''
        eco_fare_code = ''
        bus_fare_code = ''
        first_fare_code = ''
        for j in range(0,len(totalFareDetails)):
            cabintype = ''
            miles = 0
            taxes = 0 
            fareCode=[]
            if totalFareDetails[j]['cabinName'] != None:
                tax = 0
                fareCodeHolder = totalFareDetails[j]['miscFlightInfos']
                for c in range(0,len(fareCodeHolder)):
                    fareCabin = fareCodeHolder[c]['cabinName']
                    bookingCode = fareCodeHolder[c]['displayBookingCode']
                    fareCode.append(bookingCode)
                    bookingCode = bookingCode+" "+fareCabin
                cabinName = totalFareDetails[j]['cabinName']
                miles = totalFareDetails[j]['totalAwardMiles']
                if ',' in miles:
                    miles = miles.replace(',','')
                taxInt = totalFareDetails[j]['totalPriceLeft']
                if ',' in taxInt:
                    taxInt = taxInt.replace(',','')
                taxFloat = totalFareDetails[j]['totalPriceRight']
                if taxFloat == '' or taxFloat == None:
                    taxFloat = 0
                tax = float(taxInt)+float(taxFloat)
                currencyCode = totalFareDetails[j]['currencyCode']
                if currencyCode and currencyCode != 'USD': 
                    currencychange = urllib.urlopen("https://www.exchangerate-api.com/%s/%s/%f?k=e002a7b64cabe2535b57f764"%(currencyCode,"USD",float(tax)))
                    taxes = currencychange.read()
                else:
                    taxes = tax
            if len(pricecol) > 1:
                
                if j == 0:
                    cabintype = "Economy"
                if j == 1 and 'First' not in pricecol[1].text:
                    cabintype = "Business"
                if j == 2 and len(pricecol) > 2 and 'First' not in pricecol[2].text:
                    cabintype = "Business"
            else:
                if len(pricecol) > 0 and len(pricecol) < 2:
                    if 'Main Cabin' in pricecol[0].text:
                        cabintype = "Economy"
                    elif 'First' not in pricecol[0].text:
                        cabintype = 'Business'
            if 'Economy' in cabintype:
                ecofare = miles
                echoTax = taxes
                cabintype1 = "Economy"
                if len(fareCode) > 0:
                    eco_fare_code = ','.join(fareCode)
                    ecofareClass = ' Economy@'.join(fareCode)+' Economy'
                    ecofareClass = ecofareClass
            elif 'Business' in cabintype:
                cabintype2 = "Business"
                bussfare = miles
                busstax = taxes
                if len(fareCode) > 0:
                    bus_fare_code = ','.join(fareCode)
                    bussFareClass = ' Business@'.join(fareCode)+' Business'
            else:
                cabintype3 = "First"
                firstFare = miles
                firsttax = taxes
                if len(fareCode) > 0:
                    first_fare_code = ','.join(fareCode)
                    firstFareClass = ' First@'.join(fareCode)+' First'
        departdetailtext = '@'.join(departDetail)
        ariveDetailtext = '@'.join(ariveDetail)
        flightDetailtext = '@'.join(flightDetail)
        operatorDetailtext = '@'.join(operatorDetail)
        stoppage = ''
        stop = int(len(departDetail) - 1)
        if stop == 0:
            stoppage = "NONSTOP"
        elif stop == 1:
            stoppage = "1 STOP"
        else:
            stoppage = str(stop)+" STOPS"
        arivalTime1 = (datetime.datetime.strptime(arivalTime, '%I:%M%p'))
        arivalTime = arivalTime1.strftime('%H:%M')
        departTime1 = (datetime.datetime.strptime(departTime, '%I:%M%p'))
        departTime = departTime1.strftime('%H:%M')

        if len(pricecol) > 1 and 'Delta Comfort+' in pricecol[1].text:
            bussFareClass = bussFareClass.replace('Business', 'Economy')
            values_string.append((flightNo, str(searchkey), stime, stoppage, "test", SourceCOde, destinationCode, departTime, arivalTime, tripDuration, str(ecofare), str(echoTax), '0', '0', str(firstFare), str(firsttax), cabintype1, cabintype2, cabintype3, "delta", departdetailtext, ariveDetailtext, flightDetailtext, operatorDetailtext,ecofareClass,'',firstFareClass,eco_fare_code,'',first_fare_code))
            values_string.append((flightNo, str(searchkey), stime, stoppage, "test", SourceCOde, destinationCode, departTime, arivalTime, tripDuration, str(bussfare), str(busstax), '0', '0', '0', '0', cabintype1, cabintype2, cabintype3, "delta", departdetailtext, ariveDetailtext, flightDetailtext, operatorDetailtext,bussFareClass,'','',bus_fare_code,'',''))
        else:
            values_string.append((flightNo, str(searchkey), stime, stoppage, "test", SourceCOde, destinationCode, departTime, arivalTime, tripDuration, str(ecofare), str(echoTax), str(bussfare), str(busstax), str(firstFare), str(firsttax), cabintype1, cabintype2, cabintype3, "delta", departdetailtext, ariveDetailtext, flightDetailtext, operatorDetailtext,ecofareClass,bussFareClass,firstFareClass,eco_fare_code,bus_fare_code,first_fare_code))
        if len(values_string) > 50:
            if not DEV_LOCAL:
                cursor.executemany ("INSERT INTO pexproject_flightdata (flighno,searchkeyid,scrapetime,stoppage,stoppage_station,origin,destination,departure,arival,duration,maincabin,maintax,firstclass,firsttax,business,businesstax,cabintype1,cabintype2,cabintype3,datasource,departdetails,arivedetails,planedetails,operatedby,economy_code,business_code,first_code,eco_fare_code,business_fare_code,first_fare_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", values_string)
                db.commit()
            else:
                print values_string
            values_string =[]
            
    if len(values_string) > 0:
        if not DEV_LOCAL:
            cursor.executemany ("INSERT INTO pexproject_flightdata (flighno,searchkeyid,scrapetime,stoppage,stoppage_station,origin,destination,departure,arival,duration,maincabin,maintax,firstclass,firsttax,business,businesstax,cabintype1,cabintype2,cabintype3,datasource,departdetails,arivedetails,planedetails,operatedby,economy_code,business_code,first_code,eco_fare_code,business_fare_code,first_fare_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", values_string)
            db.commit()
        else:
            print values_string

    storeFlag(searchkey,stime)               
    return searchkey
            
            
if __name__=='__main__':
    delta(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[5])
    print '\t@@@@ delta finished'
    # delta('ewr', 'msp', '12/29/2016', '213141231')        
