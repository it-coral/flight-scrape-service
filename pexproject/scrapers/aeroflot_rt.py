import os, sys
from bs4 import BeautifulSoup
from selenium import webdriver
import datetime
from datetime import timedelta
import time
import re
from pyvirtualdisplay import Display
import json
import codecs
import requests
import HTMLParser

DEBUG = True
# DEBUG = False
DEV_LOCAL = False
# DEV_LOCAL = True

if not DEV_LOCAL:
    import customfunction

TAXES = {
    'AE': 'maintax',        # Economy
    'AC': 'firsttax',       # Comfort
    'AB': 'businesstax',    # Business
}

URL = ('https://reservation.aeroflot.ru/SSW2010/7B47/webqtrip.html?'
       'searchType=NORMAL&journeySpan=RT&alternativeLandingPage=1&lang=en&'
       'currency=USD&referrerCode=AFLBOOK&numAdults=1&numChildren=0&'
       'utm_source=&utm_campaign=&utm_medium=&'
       'utm_content=&utm_term=&isAward=1&origin=%s&destination=%s'
       '&departureDate=%s&returnDate=%s')

FLIGHT_URL = 'https://reservation.aeroflot.ru/SSW2010/7B47/webqtrip.html'

CONTEXTOBJECT = (
    '{"transferObjects":[{"componentType":"cart","actionCode":"checkPrice"'
    ',"queryData":{"componentId":"cart_1","componentType":"cart","actionCo'
    'de":"checkPrice","queryData":null,"requestPartials":["initialized"],"'
    'selectedBasketRefs":[%s,%s]}}]}'
)

DATA = {
    '_eventId_ajax': '',
    'execution': None,
    'ajaxSource': 'true',
    'contextObject': None
}

def get_cookie(driver, name, path):
    cookies = driver.get_cookies()
    for cookie in cookies:
        if (cookie['name'] == name and cookie['path'].strip('/') == path.strip('/')):
            return cookie['value']
    return None

def aeroflot(ocity_code, dcity_code, searchdate, searchkey, returndate, returnkey):
    display = Display(visible=0, size=(800, 600))
    display.start()
    chromedriver = "/usr/bin/chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    
    driver = webdriver.Chrome(chromedriver)
    url = URL % (ocity_code, dcity_code, searchdate, returndate)

    driver.get(url)
    execution = driver.current_url[-4:]
    DATA['execution'] = execution

    sys.stdout=codecs.getwriter('utf-8')(sys.stdout)
    log_path = 'aeroflot_rt_log' if DEV_LOCAL else '/home/upwork/aeroflot_rt_log'
    log_file = open(log_path, 'a') if DEBUG else sys.stdout
    log_file.write('\n\n'+'='*70+'\n\n')    
    log_file.write(url+'\n\n')

    db = customfunction.dbconnection() if not DEV_LOCAL else None
    currentdatetime = datetime.datetime.now()
    stime = currentdatetime.strftime('%Y-%m-%d %H:%M:%S')
    flightinfo = []

    try:
        html_page = driver.page_source
        soup = BeautifulSoup(html_page,"lxml")

        radio_id = soup.find('input', id=re.compile('^flight_outbounds_'))['id']
        radio = driver.find_element_by_id(radio_id)

        time.sleep(1)
        radio.click()
        cookies = {
            'JSESSIONID': get_cookie(driver, 'JSESSIONID', '/SSW2010'),
            'WLPCOOKIE': get_cookie(driver, 'WLPCOOKIE', '/SSW2010'),
        }

        html_page = driver.page_source
        json_text = re.search(r'^\s*var templateData = \s*({.*?})\s*;\s*$', html_page, flags=re.DOTALL | re.MULTILINE).group(1)
        jsonData = json.loads(json_text)
        
        model = jsonData["rootElement"]["children"][1]["children"][0]["children"][5]["model"]
        brandedInOutMappings = model["brandedInOutMappings"]
        tax = get_tax(cookies, brandedInOutMappings) / 2
        valid_refs = get_valid_ref(brandedInOutMappings)
        log_file.write(str(valid_refs)+' ####\n')
        tempdata = model["allItineraryParts"]

        for k in range(0,len(tempdata)):            
            segments = tempdata[k]["segments"]
            rowRecord = tempdata[k]["itineraryPartData"]
            fltno = ''

            origin = rowRecord["departureCode"]
            dest = rowRecord["arrivalCode"]
            departureDate = rowRecord["departureDate"]
            deptDateTime = departureDate.split(" ")

            originDetails = []
            destDetails = []
            flightsDetails =[]
            operatorCarrier = []
            for counter in range (0,len(segments)):
                bookingCode = segments[counter]['bookingClass']
                bookingClassCabin = segments[counter]['allClassOfService']
                segOrigin = segments[counter]["departureCode"]
                segDepartDate = segments[counter]["departureDate"]
                segDetailFormat = segDepartDate[:-3]+" | from "+segOrigin
                originDetails.append(segDetailFormat)
                
                segDest = segments[counter]["arrivalCode"]
                segArive = segments[counter]["arrivalDate"]
                destdetailFormat = segArive[:-3]+" at "+segDest
                destDetails.append(destdetailFormat)
                operatorCarrier.append('Aeroflot')
                
            deptDate = deptDateTime[0]
            dt1 = datetime.datetime.strptime(deptDate, '%Y/%m/%d')
            deptDate = dt1.strftime('%Y-%m-%d')

            depttime = deptDateTime[1]
            depttime1 = (datetime.datetime.strptime(depttime, '%H:%M:%S'))
            departtime = depttime1.strftime('%H:%M')
            arrivalDate = rowRecord["arrivalDate"]
            arrivalDateTime = arrivalDate.split(" ")
            arivaldt = arrivalDateTime[0]
            arivalTime = arrivalDateTime[1]
            arivalTime1 = (datetime.datetime.strptime(arivalTime, '%H:%M:%S'))
            arive = arivalTime1.strftime('%H:%M')
            totalTripDuration = rowRecord["totalTripDuration"]
            
            totalMinte = (int(totalTripDuration)/60000)
            hr = totalMinte/60
            minute = totalMinte % 60
            tripDuration = str(hr)+"h "+str(minute)+"m"
            departureCodes = rowRecord["departureCodes"]
            operatingCarrier = rowRecord["operatingCarrier"]
            flightDurations = rowRecord["flightDurations"]
            
            flightNumber = rowRecord["flightNumber"]
            airlineCodes = rowRecord["airlineCodes"]
            aircraftType = rowRecord["aircraftType"]

            for f in range(0,len(flightNumber)):
                flightNo = airlineCodes[f]+" "+str(flightNumber[f])
                if f == 0:
                    fltno = flightNo
                fltTime = flightDurations[f]
                fltMinuteTime = int(fltTime)/60000
                fltMinuteTimeHour = fltMinuteTime/60
                fltMinuteTime = fltMinuteTime % 60
                fltTimeFormat = str(fltMinuteTimeHour)+"h "+str(fltMinuteTime)+"m"
                fltFormat = flightNo+" | "+aircraftType[f]+" ("+fltTimeFormat+")"
                flightsDetails.append(fltFormat)

            originDetailString = '@'.join(originDetails)
            arivedetailtext = '@'.join(destDetails)
            planedetailtext = '@'.join(flightsDetails)
            operatortext = ''
            if len(operatorCarrier) > 0:
                operatortext = '@'.join(operatorCarrier)
            noOfStop = len(departureCodes) - 1
            stoppage = ''
            if noOfStop == 0:
                stoppage = "NONSTOP"
            elif noOfStop == 1:
                stoppage = "1 STOP"
            else:
                stoppage = str(noOfStop)+" STOPS"
            
            allPrices = tempdata[k]["basketsRef"]
            economy = 0
            ecotax = 0
            business = 0
            businesstax = 0
            first = 0
            firsttax = 0
            for key in allPrices:
                farePrices = allPrices[key]["prices"]["moneyElements"] #["priceAlternatives"]
                if int(allPrices[key]['brandedBasketHashRef']) not in valid_refs:
                    continue

                miles = farePrices[0]["moneyTO"]["amount"]
                if 'AE' in key:     # X Economy
                    economy = miles 
                    ecotax = tax
                elif 'AB' in key:   # O Business
                    business = miles
                    businesstax = tax
                elif 'AC' in key:   # F Comfort
                    first = miles
                    firsttax = tax

            searchkeyid = returnkey
            if deptDate == searchdate:
                searchkeyid = searchkey

            if economy or business:
                flightinfo.append(('Flight '+str(fltno), searchkeyid, stime, stoppage, "test", origin, dest, departtime, arive, tripDuration, str(economy), str(ecotax), str(business),str(businesstax), str(0), str(0), "Economy", "Business", "First", "aeroflot", originDetailString, arivedetailtext, planedetailtext, operatortext, 'X Economy', 'O Business', 'First', 'X', 'O', 'I'))
            if first:
                flightinfo.append(('Flight '+str(fltno), searchkeyid, stime, stoppage, "test", origin, dest, departtime, arive, tripDuration, str(first), str(firsttax), str(0),str(0), str(0), str(0), "Economy", "Business", "First", "aeroflot", originDetailString, arivedetailtext, planedetailtext, operatortext, 'F Comfort', 'O Business', 'First', 'F', 'O', 'I'))

        log_file.write(str(flightinfo))
        log_file.write('\n')
    except Exception, e:
        log_file.write('Error Message: '+str(e)+'\n')
        log_file.write('Error or No data!\n\n')

    if not DEV_LOCAL:
        cursor = db.cursor()
        cursor.executemany("INSERT INTO pexproject_flightdata (flighno,searchkeyid,scrapetime,stoppage,stoppage_station,origin,destination,departure,arival,duration,maincabin,maintax,firstclass,firsttax,business,businesstax,cabintype1,cabintype2,cabintype3,datasource,departdetails,arivedetails,planedetails,operatedby,economy_code,business_code,first_code,eco_fare_code,business_fare_code,first_fare_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", flightinfo)
        db.commit()
        cursor.execute ("INSERT INTO pexproject_flightdata (flighno,searchkeyid,scrapetime,stoppage,stoppage_station,origin,destination,duration,maincabin,maintax,firstclass,firsttax,business,businesstax,cabintype1,cabintype2,cabintype3,datasource,departdetails,arivedetails,planedetails,operatedby,economy_code,business_code,first_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", ("flag", returnkey, stime, "flag", "test", "flag", "flag", "flag", "0","0", "0","0", "0", "0", "flag", "flag", "flag", "aeroflot", "flag", "flag", "flag", "flag", "flag", "flag", "flag"))
        db.commit()                      
        cursor.execute ("INSERT INTO pexproject_flightdata (flighno,searchkeyid,scrapetime,stoppage,stoppage_station,origin,destination,duration,maincabin,maintax,firstclass,firsttax,business,businesstax,cabintype1,cabintype2,cabintype3,datasource,departdetails,arivedetails,planedetails,operatedby,economy_code,business_code,first_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", ("flag", searchkey, stime, "flag", "test", "flag", "flag", "flag", "0","0", "0","0", "0", "0", "flag", "flag", "flag", "aeroflot", "flag", "flag", "flag", "flag", "flag", "flag", "flag"))
        db.commit()   
    display.stop()
    driver.quit()              
    log_file.close()
    return searchkey    
           
def get_valid_ref(brandedInOutMappings):
    refs = []
    for key, mappings in brandedInOutMappings.items():
        if mappings:
            refs.append(int(key))
            refs = refs + mappings
    return refs

def get_tax(cookies, brandedInOutMappings): 
    for key, mappings in brandedInOutMappings.items():
        if mappings:
            fref1 = key
            fref2 = mappings[0]
            break

    DATA['contextObject'] = [CONTEXTOBJECT % (fref1, fref2)]
    resp = requests.post(
        FLIGHT_URL,
        cookies=cookies,
        data=DATA,
    )
    resp_html = resp.json()['content'][0]['partials']['initialized']
    h = HTMLParser.HTMLParser()
    resp_html = h.unescape(resp_html)
    taxsoup = BeautifulSoup(resp_html, 'lxml')
    # log_file.write(resp_html.encode('utf8')) 
    # log_file.write('\n\n')

    tax_amount = taxsoup.find('div', class_='total-top').find_all(
        'span', class_='prices-amount')
    
    if len(tax_amount) > 0:
        return float(tax_amount[1].text)

    return 0
 
if __name__=='__main__':
    aeroflot(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    # aeroflot('MOW', 'NYC', '2016-06-25', '265801', '2016-07-20')
    # aeroflot('PEK', 'MOW', '2016-06-30', '265801', '2016-07-27')