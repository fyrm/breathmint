#!/usr/bin/python3
'''
breathmint
	Burp Issues XML Parser

	typical workflow:
	0. find_burp_output(directory) -> returns list of files ("burp_file_list")
	1. parse_files(file_list=burp_file_list) -> returns list of all issues ("all_issues")
		uses make_me_pretty to clean up output content
	2. create_output - using excelsify
		a. create_worksheet_data() for each worksheet you wish to include in the workbook
			i. make a list of column names to be included in the worksheet (output_column_names)
			ii. create_worksheet_data(output_column_names=output_column_names, issue_data_list=all_issues) -> returns dictionary; use as input to "excelsify_worksheet_data"
		b. excelsify.create_workbook(worksheet_data=excelsify_worksheet_data, out_filename=excelsify_workbook_name)
'''

#
#
# -- import public modules --
#
#
import xml.etree.ElementTree as ET
import argparse
import os
import datetime
import traceback
import sys
import re
import html
import unicodedata

#
#
# -- import private modules --
#
#
import excelsify
import make_me_pretty

#
#
# -- Global variables --
#
#
RISK_VALUES = ["Critical", "High", "Medium", "Low", "Informational"]
RISK_SYNONYM_MAPPING = {'None':"Informational", 'Info':"Informational", 'Information':"Informational", 'Moderate':"Medium"}
SORT_ORDER_RISK = {"Critical":0, "High":1, "Medium":2, "Low":3, "Informational":4}

#
#
# -- Function declarations --
#
#

#
#
#	breathmint_logo
#
#		tis a silly little function to return a logo as a string
#
#
def breathmint_logo():
	try:
		retval = ""
		retval = retval + "                              /||-----||/\n"
		retval = retval + "                            |-------------|/\n"
		retval = retval + "                           -----------------|\n"
		retval = retval + "                          |------------------/\n"
		retval = retval + "                          //////////|--------|\n"
		retval = retval + ".......--------------------------------------|      ////\n"
		retval = retval + "_......-------------------------------------/  /||--------||\n"
		retval = retval + "-......------------------------------------/  |--------------|\n"
		retval = retval + "/......----------------------------------/   ------------------\n"
		retval = retval + " --------------------------||||||||||||/    |------------------|\n"
		retval = retval + "  ___________________________________________//////////|-------|\n"
		retval = retval + "  /........----------------------------------------------------|\n"
		retval = retval + "   /.......----------------------------------------------------/\n"
		retval = retval + "    /_.....--------------------------------------------------/\n"
		retval = retval + "      -....------------------------------------------------|/\n"
		retval = retval + "       --------------------------------------------------//\n"
		retval = retval + "          ______________________________________\n"
		retval = retval + "           /-..._________------------------------|\n"
		retval = retval + "              |-_________--------------------------/\n"
		retval = retval + "                 /|-_____---------------------------/\n"
		retval = retval + "                      /||---------------------------|\n"
		retval = retval + "                                 //////////|--------|\n"
		retval = retval + "                                 |------------------/\n"
		retval = retval + "                                  -----------------|\n"
		retval = retval + "                                   |-------------|/\n"
		retval = retval + "                                     /||-----||/\n"
		retval = retval + "\n\nby FYRM Associates\n"
		return retval
	except Exception as e:
		print('\n==== Exception ====\n  breathmint.breathmintLogo()\n----')
		print(e)
		traceback.print_exc()
		print('\n===================')
		print('(this is really embarrassing)')
		return 'breathmint'


#
#
#	find_burp_output
#
#		find all Burp output files in the given directory
#
#
def find_burp_output(directory):
	try:
		files = []
		for file in os.listdir(directory):
			if (file.endswith(".xml") and not file.startswith("~$")):
				print('Found ' + file)
				files.append(file)
			else:
				continue
		return files
	except Exception as e:
		print('\n==== Exception ====\n  breathmint.find_burp_output()\n----')
		print(e)
		traceback.print_exc()
		print("===================")
		return []


#
#
#	parse_atags_in_html_string
#
#		get the url and displaytext from the html string
#		useful for the references and classification content in Burp XML output
#
#		the references item is a single string containing HTML tags: <ul>, <li>, <a>
#		e.g.
#			<ul>
#			<li><a href="https://developer.mozilla.org/en-US/docs/Web/Security/HTTP_strict_transport_security">HTTP Strict Transport Security</a></li>
#			<li><a href="http://www.thoughtcrime.org/software/sslstrip/">sslstrip</a></li>
#			<li><a href="https://hstspreload.appspot.com/">HSTS Preload Form</a></li>
#			</ul>
#		e.g.
#			<ul><li><a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/X-Frame-Options">X-Frame-Options</a></li></ul>
#
#		parameters:
#			html_string - something that looks like the examples above
#
#		returns:
#			[{'url':"<<url_0>>", 'displaytext':"<<displaytext_0>>"}, ..., {'url':"<<url_n>>", 'displaytext':"<<displaytext_n>>"}]
#
#
def parse_atags_in_html_string(html_string):
	retval = []
	try:
		html_string = html_string.strip()
		#	remove both opening and closing HTML list tags (<ul>, </ul>, <li>, </li>)
		html_string = re.sub(r'</*ul>', '', html_string)
		html_string = re.sub(r'</*li>', '', html_string)
		#	split at the </a> closing tags
		html_string_list = html_string.split('</a>')
		for each_reference in html_string_list:
			each_reference = each_reference.strip()
			if len(each_reference) > 0:
				#	remove the <a part of opening tag including the href syntax
				#	either single quote or double quote might be used so just remove both
				#		there's a single regex that could do this, but i don't feel like searching stackoverflow for it
				each_reference = re.sub(r'<a href="', '', each_reference)
				each_reference = re.sub(r"<a href='", '', each_reference)
				#	then split at the "> characters to separate the URL from the user-friendly link display text
				url_displaytext_split = each_reference.split('">')
				#	and in case '> was used instead of ">, do this:
				if len(url_displaytext_split) == 1:
					url_displaytext_split = each_reference.split("'>")
				url = url_displaytext_split[0].strip()
				displaytext = url_displaytext_split[1].strip()
				retval.append({'url':url, 'displaytext':displaytext})
	except Exception as e:
		print('\n==== Exception ====\n  breathmint.parse_atags_in_html_string()\n----')
		print(e)
		traceback.print_exc()
		print('\n===================')
	return retval


#
#
#	parse_files
#
#		parse the given file list
#
#		parameters:
#			file_list - list of files; output from find_burp_output function
#			risk_excluded - specifically excluded risk ratings
#							will check for both the Burp "severity" value and the mapped values in RISK_SYNONYM_MAPPING[severity]
#							will continue to next issue if the current issue has a matching risk value
#			risk_included - specifically included risk ratings
#							if empty list then all will be included
#
#		returns:
#			all_issues - see the comment in the __main__ function for details
#
#
def parse_files(file_list, risk_excluded=[], risk_included=[]):
	all_issues = []
	try:
		print("<< Parsing Burp files >>")
		for file in file_list:
			print("Parsing: " + str(file) + "\n...")
			try:
				#
				#	Get XML tree/root
				tree = ET.parse(file)
				root = tree.getroot()
				#
				#	"maximum effort" to verify this is actually a Burp xml file
				#		- Deadpool
				try:
					burp_version = root.get('burpVersion')
					if (burp_version == None or burp_version == ""):
						print("Warning: parse_files: the file \"" + str(file) + "\" does not appear to be a Burp xml issue export file")
						continue
				except:
					print("Warning: parse_files: the file \"" + str(file) + "\" does not appear to be a Burp xml issue export file")
					continue
				issue_count = 0
				for issue in root.findall('issue'):
					#
					#	Generic issue data mapping (breathmint <-> burp.xml):
					#		serial_number <-> serialNumber
					#		background <-> issueBackground
					#		remediation <-> remediationBackground
					#		references <-> references
					#		classification <-> vulnerabilityClassifications
					#
					serial_number = str(issue_count)
					if not issue.find('serialNumber') == None:
						serial_number = issue.find('serialNumber').text
					name = issue.find('name').text
					background = ""
					if not issue.find('issueBackground') == None:
						background = issue.find('issueBackground').text
						background = unicodedata.normalize("NFKD", background)
						background = make_me_pretty.fix_spacing_issues(contents=background)
						background = make_me_pretty.remove_lxml_markup(contents=background)
					remediation = ""
					if not issue.find('remediationBackground') == None:
						remediation = issue.find('remediationBackground').text
						remediation = unicodedata.normalize("NFKD", remediation)
						remediation = make_me_pretty.fix_spacing_issues(contents=remediation)
						remediation = make_me_pretty.remove_lxml_markup(contents=remediation)
					if not issue.find('remediationDetail') == None:
						remediation_detail = issue.find('remediationDetail').text
						if (not remediation_detail == None and not remediation_detail == ""):
							remediation_detail = unicodedata.normalize("NFKD", remediation_detail)
							remediation_detail = make_me_pretty.fix_spacing_issues(contents=remediation_detail)
							remediation_detail = make_me_pretty.remove_lxml_markup(contents=remediation_detail)
							if (not remediation_detail == "" and not remediation_detail == "Enter Remediation Detail..."):
								remediation += "\n" + remediation_detail
					references = []
					if not issue.find('references') == None:
						parsed_atags = parse_atags_in_html_string(html_string=issue.find('references').text)
						#	let's just keep the actual URLs, not the display text
						for atag_dict in parsed_atags:
							references.append(atag_dict['url'])
					classification = []
					if not issue.find('vulnerabilityClassifications') == None:
						parsed_atags = parse_atags_in_html_string(html_string=issue.find('vulnerabilityClassifications').text)
						#	let's just keep the actual URLs, not the display text
						for atag_dict in parsed_atags:
							classification.append(atag_dict['url'])
					#
					#	Modifiable issue data mapping (breathmint <-> burp.xml):
					#		severity <-> severity
					#		confidence <-> confidence
					#
					severity = ""
					risk = ""
					if not issue.find('severity') == None:
						severity = issue.find('severity').text
						risk = severity
						if risk in RISK_SYNONYM_MAPPING.keys():
							risk = RISK_SYNONYM_MAPPING[risk]
					if not risk in SORT_ORDER_RISK.keys():
						print("ERROR: unexpected risk (" + risk + ")")
					if risk in risk_excluded:
						continue
					elif (not risk_included == [] and not risk in risk_included):
						continue
					else:
						confidence = ""
						if not issue.find('confidence') == None:
							confidence = issue.find('confidence').text
						#
						#	Target data mapping (breathmint <-> burp.xml):
						#		ip <-> host ip
						#		uri <-> host
						#		port <-> None (port is determined using uri value)
						#		path <-> path
						#		location <-> location
						#
						#	note: ip and uri is in the <host> tag with the following format:
						#			<host ip="10.1.2.3">https://www.example.org</host>
						#
						ip = issue.find('host').get('ip')
						uri = issue.find('host').text
						fqdn = ""
						port = "443"
						protocol = "https"
						uri_split = uri.split(':')
						if len(uri_split) == 3:
							fqdn = re.sub(r'//', '', uri_split[1])
							port = uri_split[2]
						elif len(uri_split) == 2:
							fqdn = re.sub(r'//', '', uri_split[1])
							if uri_split[0] == "http":
								port = "80"
								protocol = "http"
							elif uri_split[0] == "https":
								port = "443"
							else:
								print("TODO: add default port number assignment to the code; protocol observed:", uri_split[0])
						path = ""
						if not issue.find('path') == None:
							path = issue.find('path').text
						location = ""
						if not issue.find('location') == None:
							location = issue.find('location').text
						#
						#	sometimes burp results put the same value in path and location, in which case it seems like location is really just the path
						if location == path:
							location = ""
						#
						#	Additional details data mapping (breathmint <-> burp.xml):
						#		target_details <-> issueDetailItems
						#		issue_details <-> issueDetail
						#		issue_details <-> issueDetailItems (list with all issueDetail text)
						#		requestresponse <-> requestresponse
						#
						target_details = []
						if not issue.find('issueDetailItems') == None:
							for item_detail in issue.find('issueDetailItems').iter('issueDetailItem'):
								target_details.append(item_detail.text)
						issue_details = ""
						if not issue.find('issueDetail') == None:
							issue_details = issue.find('issueDetail').text
							issue_details = unicodedata.normalize("NFKD", issue_details)
							issue_details = re.sub('&nbsp;', '', issue_details)
							issue_details = make_me_pretty.fix_spacing_issues(contents=issue_details)
							issue_details = make_me_pretty.remove_lxml_markup(contents=issue_details)
							if not issue.find('issueDetailItems') == None:
								for item_detail in issue.find('issueDetailItems').iter('issueDetailItem'):
									new_detail = unicodedata.normalize("NFKD", item_detail.text)
									new_detail = make_me_pretty.fix_spacing_issues(contents=new_detail)
									new_detail = make_me_pretty.remove_lxml_markup(contents=new_detail)
									issue_details += "\n" + new_detail
						#
						#	some burp extensions do not populate the background, remediation, and other fields properly
						#		and instead throw everything into 'issueDetail'
						#
						if background == "":
							background = issue_details
						requestresponse = {}
						request_count = 0
						response_count = 0
						if not issue.find('requestresponse') == None:
							for request in issue.find('requestresponse').iter('request'):
								requestresponse[str(request_count)] = {}
								if request.get('base64') == "true":
									requestresponse[str(request_count)]['request'] = request.text
								else:
									requestresponse[str(request_count)]['request'] = base64.b64encode(request.text.encode('utf-8', 'ignore'))
								request_count += 1
							for response in issue.find('requestresponse').iter('response'):
								if response.get('base64') == "true":
									requestresponse[str(response_count)]['response'] = response.text
								else:
									requestresponse[str(response_count)]['response'] = base64.b64encode(response.text.encode('utf-8', 'ignore'))
								response_count += 1
						#
						#	now that we have all the data, add it to all_issues with user-friendly field names as keys
						new_issue = {}
						new_issue['Serial Number'] = serial_number
						new_issue['Vulnerability Name'] = name
						new_issue['Background'] = background
						#
						#	might be fun to determine a product name for common apps, but that is for another day
						#	just a placeholder for now
						new_issue['Product Name'] = ""
						new_issue['Remediation'] = remediation
						new_issue['References'] = references
						new_issue['Classification'] = classification
						new_issue['Risk'] = risk
						new_issue['Severity'] = severity
						new_issue['Confidence'] = confidence
						new_issue['IP'] = ip
						new_issue['URI'] = uri
						new_issue['FQDN'] = fqdn
						new_issue['Port'] = port
						new_issue['Protocol'] = protocol
						new_issue['Path'] = path
						new_issue['Location'] = location
						new_issue['Target Details'] = target_details
						new_issue['Issue Details'] = issue_details
						new_issue['Request Response'] = requestresponse
						all_issues.append(new_issue)
						issue_count += 1
			except Exception as e:
				print("===================")
				print("\nERROR: breathmint.parse_files: Exception thrown when parsing file: ", str(file))
				print(e)
				traceback.print_exc()
				print("\n\t  moving on to next file")
				print("===================")
			print("Finished: " + str(file))
		print("<< Finished parsing Burp files >>")
		all_issues.sort(key=lambda k: SORT_ORDER_RISK[k['Risk']])
	except Exception as e:
		print('\n==== Exception ====\n  breathmint.parse_files()\n----')
		print(e)
		traceback.print_exc()
		print('\n===================')
	return all_issues


#
#
# -- Main program execution --
#
#
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", help="Location of the directory in which the Burp issues XML files are stored (all .xml files will be opened).")
	parser.add_argument("-f", help="Name of the single Burp file you want to parse. Ignored if '-d' option is used.")
	parser.add_argument("-e", help="('-e <comma,separated,list>') List of risk ratings to exclude from output; partial starting characters accepted; no spaces (default == none excluded).")
	parser.add_argument("-i", help="('-i <comma,separated,list>') List of severity ratings to include in output; partial starting characters accepted; no spaces (default == include all).")
	parser.add_argument("-o", help="Base name of output file(s) to which you want the parsed results to be written.")
	args = parser.parse_args()

	print("\n\n" + breathmint_logo() + "\n\nRunning breathmint\n...\n")
	print("<< Finding Burp output files >>")
	file_list = []
	try:
		if args.d:
			file_list = find_burp_output(args.d)
		elif args.f:
			file_list.append(args.f)
		else:
			print("No directory or file argument provided. Trying current directory.")
			file_list = find_burp_output('.')
	except Exception as e:
		print("===================")
		print("\nERROR: breathmint.__main__: Something went wrong when trying to get .xml file(s). This is not my fault. You failed miserably and should feel bad.")
		print(e)
		traceback.print_exc()
		print("===================")
		sys.exit()
	print("<< Finished finding Burp output files >>")
	if file_list == []:
		print("\nNote: input file list is empty; that's bad. But also we're done. That's good. Better luck next time. The sprinkles are also cursed.")
		sys.exit()

	output_filename_base = "burp-output"
	try:
		if args.o:
			output_filename_base = str(args.o)
			if output_filename_base.endswith(".xml"):
				output_filename_base = output_filename_base.replace(".xml", "")
			elif output_filename_base.endswith(".xlsx"):
				output_filename_base = output_filename_base.replace(".xlsx", "")
			elif output_filename_base.endswith(".docx"):
				output_filename_base = output_filename_base.replace(".docx", "")
		elif len(file_list) == 1:
			output_filename_base = file_list[0].replace(".xml", "")
	except Exception as e:
		print("===================")
		print("\nERROR: breathmint.__main__: Something went wrong when trying to get output filename base:")
		print(e)
		traceback.print_exc()
		print("===================")
		sys.exit()

	risk_excluded = []
	risk_included = []
	try:
		if args.e:
			risks = args.e.split(',')
			for risk in risks:
				if risk in RISK_VALUES:
					risk_excluded.append(risk)
					print("new excluded risk added:", risk)
				else:
					for approved_risk_value in RISK_VALUES:
						if (risk.casefold() == approved_risk_value.casefold() or risk.casefold() == approved_risk_value[0].casefold() or approved_risk_value.casefold().startswith(risk.casefold())):
							risk_excluded.append(approved_risk_value)
							print("new excluded risk added:", approved_risk_value)
		if args.i:
			risks = args.i.split(',')
			for risk in risks:
				if risk in RISK_VALUES:
					risk_included.append(risk)
					print("new included risk added:", risk)
				else:
					for approved_risk_value in RISK_VALUES:
						if (risk.casefold() == approved_risk_value.casefold() or risk.casefold() == approved_risk_value[0].casefold() or approved_risk_value.casefold().startswith(risk.casefold())):
							risk_included.append(approved_risk_value)
							print("new included risk added:", approved_risk_value)
	except Exception as e:
		print("===================")
		print("\nERROR: breathmint.__main__: Something went wrong when trying to get excluded/included risks:")
		print(e)
		traceback.print_exc()
		print("===================")
		sys.exit()

	#
	#	all_issues format:
	#	[
	#		{
	#			'Serial Number':"<<serialNumber>>",
	#			'Vulnerability Name':"<<name>>",
	#			'Background':"<<issueBackground>>",
	#			'Product Name':"",
	#			'Remediation':"<<remediationBackground>>",
	#			'References':[{'url':"<<reference_0_url>>", 'displaytext':"<<reference_0_displaytext>>"}, ..., {'url':"<<reference_n_url>>", 'displaytext':"<<reference_n_displaytext>>"}],
	#			'Classification':"<<vulnerabilityClassifications>>",
	#			'Risk':"<<risk>> == severity | RISK_SYNONYM_MAPPING[severity]",		(trying to enforce a common set of risk ratings)
	#			'Severity':"<<severity>>",
	#			'Confidence':"<<confidence>>",
	#			'IP':"<<host ip>>",
	#			'URI':"<<host>>",
	#			'FQDN':"<<extracted_from_URI>>",
	#			'Port':"<<port>>",
	#			'Protocol':"<<http|https>>",		(probably http or https)
	#			'Path':"<<path>>",
	#			'Location':"<<location>>",
	#			'Target Details':["<<issueDetailItem_0>>", ..., "<<issueDetailItem_n>>"],
	#			'Issue Details':"<<issueDetail>>",
	#			'Request Response':{
	#				'0':{ 'request':"<<base64(request)>>", 'response':"<<base64(response)>>", 'redirected':True|False(<<responseRedirected>>) }, ...,
	#				'n':{ 'request':"<<base64(request)>>", 'response':"<<base64(response)>>", 'redirected':True|False(<<responseRedirected>>) }
	#			}
	#		},
	#		...,
	#		{'Serial Number':"<<serialNumber>>", ..., 'Request Response':{}}
	#	]
	#
	all_issues = []
	try:
		all_issues = parse_files(file_list=file_list, risk_excluded=risk_excluded, risk_included=risk_included)
		if all_issues == []:
			print("ERROR: breathmint.__main__: parse_files returned a blank result")
		else:
			print("<< Generating output files >>")
			#
			#	assuming files were parsed correctly, we can make the output
			excelsify_workbook_name = output_filename_base + "--parsed--" + datetime.datetime.now().strftime('%Y%m%d_%H%M') + ".xlsx"
			print("Generating:", excelsify_workbook_name)
			#
			#	pick your preferred columns in the order you want them to be placed in the output
			#	column names must match the keys in each issue dictionary in the all_issues list
			output_column_names = ["Vulnerability Name", "Background", "Remediation", "References", "Classification", "Risk", "Confidence", "URI", "Path", "Location", "Target Details", "Issue Details"]
			excelsify_worksheet_data = {}
			ws = excelsify.create_worksheet_data(output_column_names=output_column_names, issue_data_list=all_issues)
			if ws == {}:
				print("ERROR: create_worksheet_data returned a blank dictionary")
			else:
				excelsify_worksheet_data['Burp Issues'] = ws
			success = excelsify.create_workbook(worksheet_data=excelsify_worksheet_data, out_filename=excelsify_workbook_name)
			if success == True:
				print("...\nFinished:", excelsify_workbook_name)
			else:
				print("ERROR: Failed to generate excel output file:", excelsify_workbook_name)
			print("<< Finished generating output files >>")
	except Exception as e:
		print("===================")
		print("\nERROR: breathmint.__main__: Exception thrown in main execution:")
		print(e)
		traceback.print_exc()
		print("===================")
		sys.exit()
