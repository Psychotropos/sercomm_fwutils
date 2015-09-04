# Disable remote management and remote firmware updates on Sercomm's Speedport W 724 Typ C (tested on the OTE variant)
# The same effect can be achieved (assuming you have access to a busybox shell on the router) by executing:
# /usr/sbin/cmld_client set Device.ManagementServer.EnableCWMP=0
# Requires the requests module for Python, which you can acquire using pip:
# pip install requests
import requests
import sys
import re
s = requests.Session()
s.headers.update({'Accept-Language':'en-us'})

def get_value_by_vartype_and_varid(res, vartype, varid):
	for value in res:
		if value['vartype'] == vartype:
			if value['varid'] == varid:
				return value['varvalue']
	return None

def get_id_and_values_of_vartype(res, vartype):
	table = {}
	for value in res:
		if value['vartype'] == vartype:
			table[value['varid']] = value['varvalue']
	return table

def login(ip, password):
	r = s.post('http://%s/data/Login.json' % (ip), data={'password': password, 'showpw':'0'})
	result = get_value_by_vartype_and_varid(r.json(), 'status', 'login')
	if result == 'success':
		print "[+] Successfully logged into the router!"
	else:
		print "[-] Invalid credentials or rate limit enforced, failed to log in! Login lock duration: %s seconds." % (get_value_by_vartype_and_varid(decoded_res, 'value', 'login_locked'))
		sys.exit(0)

def scrape_csrf_token(ip):
	r = s.get('http://%s/html/content/internet/abuse_detect.html?lang=en' % (ip))
	m = re.search('\"sessionid\".+?value\=\"(.+?)\"\/', r.text)
	try:
		token = m.group(1)
	except IndexError:
		print "[-] Failed to find CSRF token!"
		sys.exit(0)
	return token

def get_option_field_values(ip):
	# rw module fields:
	# fields_of_interest = ['use_dyndns', 'use_abuse', 'use_telephone', 'use_dect', 'use_answering', 'use_wlan', 'use_wlan_5ghz', 'use_wps', 'use_hsfon', 'use_repeater', 'easy_support_deactive', 'autofw_deactive', 'use_external_modem', 'use_internal_modem', 'use_internet', 'use_statusbericht', 'allow_ftp', 'allow_ftps', 'use_webnwalk', 'use_webnwalk_phone', 'use_dsl']
	r = s.get('http://%s/data/Modules.json' % (ip))
	return get_id_and_values_of_vartype(r.json(), 'option')

def set_option_field_value(ip, csrf_token, field, value):
	r = s.post('http://%s/data/Modules.json' % (ip), data={'sessionid': csrf_token, field: value})
	if get_value_by_vartype_and_varid(r.json(), 'option', field) != value:
		print "[-] Requested field value change for field %s failed to propagate! Exiting." % (field)
		sys.exit(0)

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print "[-] Usage: python disable_remote_mgmt.py router_ip router_password"
		sys.exit(1)
	router_ip = sys.argv[1]
	router_password = sys.argv[2]
	print "[+] Logging into router..."
	login(router_ip, router_password)
	print "[+] Getting current settings..."
	options = get_option_field_values(router_ip)
	if bool(options['autofw_deactive']) and bool(options['easy_support_deactive']):
		print "[-] This router already has remote management disabled! Exiting."
		sys.exit(0)
	print "[+] Scraping CSRF token..."
	csrf_token = scrape_csrf_token(router_ip)
	print "[+] Disabling remote management..."
	set_option_field_value(router_ip, csrf_token, 'autofw_deactive', '1')
	set_option_field_value(router_ip, csrf_token, 'easy_support_deactive', '1')
	print "[+] Done!"
