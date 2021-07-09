""""  Code by https://github.com/NotSelwyn
 ██████╗  ██████╗  ███╗   ██╗ ███████╗ ██╗  ██████╗
██╔════╝ ██╔═══██╗ ████╗  ██║ ██╔════╝ ██║ ██╔════╝
██║      ██║   ██║ ██╔██╗ ██║ █████╗   ██║ ██║  ███╗
██║      ██║   ██║ ██║╚██╗██║ ██╔══╝   ██║ ██║   ██║
╚██████╗ ╚██████╔╝ ██║ ╚████║ ██║      ██║ ╚██████╔╝
 ╚═════╝  ╚═════╝  ╚═╝  ╚═══╝ ╚═╝      ╚═╝  ╚═════╝
"""

# Access token cookie on Udemy
access_token = ""

# Client ID cookie on Udemy
client_id = ""

# Amount of coupons to claim at once (keep in mind, if one of them fail they all fail and have to be checked individually)
chunk_size = 8

""""
 ██████╗  ██████╗  ███████╗  ███████╗
██╔════╝ ██╔═══██╗ ██╔═══██╗ ██╔════╝
██║      ██║   ██║ ██║   ██║ █████╗
██║      ██║   ██║ ██║   ██║ ██╔══╝
╚██████╗ ╚██████╔╝ ██████╔═╝ ███████╗
 ╚═════╝  ╚═════╝  ╚═════╝   ╚══════╝
"""

from json import loads
from requests import Session
from bs4 import BeautifulSoup
from time import sleep

sess = Session()
inspected_courses = []
headers = {'authorization': 'Bearer ' + access_token, 'accept': 'application/json, text/plain, */*', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0', 'x-udemy-authorization': 'Bearer ' + access_token, 'content-type': 'application/json;charset=UTF-8', }
scraped = BeautifulSoup(sess.get("https://yofreesamples.com/courses/free-discounted-udemy-courses-list").text, "html.parser").find_all("div", {"class": "col-xs-12 col-sm-9"})
for i in range(0, len(scraped), chunk_size):
    info = []
    tax_info = []
    for html in scraped[i:i+chunk_size]:
        uri = html.find('a', {'class': 'btn btn-md btn-success'}).attrs['href']
        cc = uri.split("/?couponCode=")[1]
        cid = str(loads(BeautifulSoup(sess.get(uri).content, 'html.parser').find("body").attrs['data-module-args'])['course_id'])
        info.append('{"discountInfo": {"code": "' + cc + '"}, "buyable": {"type": "course", "id":' + cid + ', "context": {}}, "price": {"amount": 0, "currency": "EUR"}}')
        tax_info.append('{"tax_amount":0,"udemy_txn_item_reference":"course-' + cid + '","tax_excluded_amount":0,"tax_included_amount":0}')
    data = '{"checkout_environment":"Marketplace","checkout_event":"Submit","shopping_info":{"items": [' + ','.join(info) + '], "is_cart":true},"payment_info":{"payment_vendor":"Free","payment_method":"free-method"},"tax_info":{"tax_rate":21,"billing_location":{"country_code":"NL","secondary_location_info":null},"currency_code":"eur","transaction_items":[' + ','.join(tax_info) + '],"tax_breakdown_type":"tax_inclusive"}}'
    r = sess.post('https://www.udemy.com/payment/checkout-submit/', data=data, headers=headers, cookies={"access_token": access_token, "client_id": client_id}).json()
    if "status" not in r or "succeeded" not in r["status"]:
        print("(CHUNK FAILED)")
        inspected_courses.extend(scraped[i:i+chunk_size])
    else:
        print(f"(SUCCESSFULLY REDEEMED {chunk_size} COURSES)")

# Check all failed coupons individually
c = 0
i = 0
print("CLAIMED / CHECKED / TOTAL")
while i < len(inspected_courses):
    uri = inspected_courses[i].find('a', {'class': 'btn btn-md btn-success'}).attrs['href']
    info = loads(BeautifulSoup(sess.get(uri).content, 'html.parser').find("body").attrs['data-module-args'])
    url, cc = uri.split("/?couponCode=")
    s = False
    if info["is_paid"] is True:
        if "detail" not in sess.get(f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{info['course_id']}", headers=headers, cookies={"access_token": access_token, "client_id": client_id}).json():
            print(f"({c}/{i}/{len(inspected_courses)}) (INVALID: ALREADY REDEEMED) >>> {url}")
            s = True
        else:
            data = '{"checkout_environment":"Marketplace","checkout_event":"Submit","shopping_info":{"items":[{"discountInfo":{"code":"' + cc + '"},"buyable":{"type":"course","id":' + str(info["course_id"]) + ',"context":{}},"price":{"amount":0,"currency":"EUR"}}],"is_cart":true},"payment_info":{"payment_vendor":"Free","payment_method":"free-method"},"tax_info":{"tax_rate":21,"billing_location":{"country_code":"NL","secondary_location_info":null},"currency_code":"eur","transaction_items":[{"tax_amount":0,"udemy_txn_item_reference":"course-' + str(info["course_id"]) + '","tax_excluded_amount":0,"tax_included_amount":0}],"tax_breakdown_type":"tax_inclusive"}}'
            r = sess.post('https://www.udemy.com/payment/checkout-submit/', data=data, headers=headers, cookies={"access_token": access_token, "client_id": client_id}).json()
            if "status" in r and r["status"] == "succeeded":
                c += 1
                print(f"({c}/{i}/{len(inspected_courses)}) (BOUGHT) >>> {url}")
                s = True
                sleep(2)
            elif "detail" in r and "Request was throttled" in r["detail"]:
                print(f"({c}/{i}/{len(inspected_courses)}) (COOLDOWN: 10s) >>> {url}")
                sleep(10)
                s = True
                i -= 1
    if s is False:
        print(f"({c}/{i}/{len(inspected_courses)}) (INVALID: COUPON) >>> {url}")
        sleep(2)
    i += 1
