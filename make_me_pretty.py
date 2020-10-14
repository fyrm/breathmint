#!/usr/bin/python3
'''
make_me_pretty
	Take in ugly, push out pretty
'''

#
#
# -- import public modules --
#
#
import string
import re
import traceback
from bs4 import BeautifulSoup
import warnings

#
#
# -- Global variables --
#
#
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
SORT_ORDER_RISK = {"Critical":0, "High":1, "Medium":2, "Low":3, "Informational":4}
TARGET_DICT_KEYS = ["uri", "path", "details"]
TARGET_DICT_KEY_LIST_ORDERED = ['Risk', 'FQDN', 'Protocol', 'Port', 'Path']
NO_START_PUNCTUATION = set(string.punctuation) - {'/','<'}

#
#
# -- Function declarations --
#
#

#
#
#	remove_lxml_markup
#
#
def remove_lxml_markup(contents):
	retval = ""
	try:
		retval = BeautifulSoup(contents, "lxml").text
		#
		#	that was easy. thanks BeautifulSoup
		#
	except Exception as e:
		print("\n==== Exception ====\n  make_me_pretty.remove_lxml_markup()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return retval

#
#
#	safe_string_to_write
#
#		prepare a results worksheet
#
#		note: re.sub('<[^<]+?>', '', str(val)) will remove all html tags from str(val)
#
#
def safe_to_write_string(contents):
	retval = """"""
	try:
		if isinstance(contents, str):
			while any(contents.startswith(x) for x in NO_START_PUNCTUATION):
				contents = contents[1:]
			contents = contents.strip()
		if len(contents) > 0:
			if type(contents) is dict:
				for key,val in contents.items():
					if key in SORT_ORDER_RISK.keys():
						retval = retval + str(key) + """:\n"""
						retval = retval + safe_to_write_string(val)
					elif key in TARGET_DICT_KEYS:
						if len(val) == 0:
							retval = retval + """\n"""
						else:
							retval = retval + safe_to_write_string(val)
					else:
						retval = retval + str(key) + """\n"""
						if (type(val) is dict or type(val) is list):
							retval = retval + safe_to_write_string(val)
						else:
							retval = retval + str(val) + """\n"""
			elif type(contents) is list:
				for val in contents:
					if (type(val) is dict or type(val) is list):
						retval = retval + safe_to_write_string(val)
					else:
						retval = retval + str(val) + """\n"""
			else:
				retval = str(contents) + """\n"""
	except Exception as e:
		print("\n==== Exception ====\n  make_me_pretty.safe_to_write_string()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return retval


#
#
#	fix_spacing_issues
#
#		fix spacing issues within a string
#
#		this might seem like overkill, but some security tools include unnecessary whitespace chars inside individual strings
#		also this code gives up a little efficiency for easier readability and editability
#		what is it with security tools adding random whitespace in various parts of strings?
#
#
def fix_spacing_issues(contents):
	try:
		if (contents == None or contents == ''):
			return ''
		contents = contents.strip()
		while '  ' in contents:
			contents = contents.replace('  ', ' ')
		while '\n ' in contents:
			contents = contents.replace('\n ', '\n')
		while ' \n' in contents:
			contents = contents.replace(' \n', '\n')
		while ' \t' in contents:
			contents = contents.replace(' \t', '\t')
		while '\t ' in contents:
			contents = contents.replace('\t ', '\t')
		while '\n\n' in contents:
			contents = contents.replace('\n\n', '\n')
		while '\t\t' in contents:
			contents = contents.replace('\t\t', '\t')
		while '\t\n' in contents:
			contents = contents.replace('\t\n', '\n')
		while '\n;' in contents:
			contents = contents.replace('\n;', ';')
		contents = contents.replace(' :', ':')
		contents = contents.replace(' ;', ';')
		contents = contents.replace(' ,', ',')
		contents = contents.replace('( ', '(')
		contents = contents.replace(' )', ')')
		if contents.endswith('\n'):
			contents = contents[:-1]
		if contents.startswith('\n'):
			contents = contents[1:]
	except Exception as e:
		print('\n==== Exception ====\n  make_me_pretty.fix_spacing_issues()\n----')
		print(e)
		traceback.print_exc()
		print('\n===================')
	return contents


#
#
#	cut_off_string
#
#		because sometimes you want lots of details, but not like that
#
#		parameters:
#			instring - the thing that should be a string but may be another type of thing that will be turned into a string
#			char - specific character to limit; i dont expect this to be anything other than '\n'
#			max_char - maximum number of instances of char in the result string
#
#
def cut_off_string(instring, char, max_char):
	retval = ""
	try:
		instring_split = ""
		if isinstance(instring, list):
			instring_split = '\n'.join(instring)
		elif isinstance(instring, dict):
			for key,val in instring:
				instring_split += str(key) + '\n' + str(val) + '\n'
		instring_split = instring.split(char)
		iteration_cap = min(len(instring_split), max_char)
		for i in range(iteration_cap):
			retval += instring_split[i] + str(char)
	except Exception as e:
		print('\n==== Exception ====\n  make_me_pretty.cut_off_string()\n----')
		print(e)
		traceback.print_exc()
		print('\n===================')
	return retval


#
#
#	target_pretty
#
#		a target-specific version of safe_to_write_string
#			where a target is a dictionary defined by various types of data
#
#		parameters:
#			target_dict - has the following items:
#				{
#					'FQDN':"<<FQDN>>",
#					'Protocol':"<<Protocol>>",
#					'Port':"<<Port>>",
#					'Path':"<<Path>>",
#					'Details':["<<str_0>>", ..., "<<str_n>>"]
#				}
#			include_details - True|False for whether the 'Details' in target_dict should be added to the return string
#			details_separator - how to separate the list items in target_dict['Details']
#
#		returns:
#			a string version of the input target_dict
#
#
def target_pretty(target_dict, include_details=False, details_separator="\n"):
	retval = """"""
	try:
		protocols_in_front_list = ['http', 'https', 'ssh', 'sftp', 'ftp', 'smb']
		if target_dict['Protocol'] in protocols_in_front_list:
			retval = target_dict['Protocol'] + """://"""
		retval += target_dict['FQDN']
		if (not target_dict['Port'] == "0" and not target_dict['Port'] == 0):
		 	retval += """:""" + str(target_dict['Port'])
		if (not target_dict['Path'] == "None" and not target_dict['Path'] == "" and not target_dict['Path'] == "/"):
			retval += target_dict['Path']
		if (include_details == True and 'Details' in target_dict.keys()):
			retval += details_separator + target_dict['Details']
	except Exception as e:
		print("\n==== Exception ====\n  make_me_pretty.target_pretty()\n----")
		print(e)
		traceback.print_exc()
		print("\n--------")
		print(target_dict)
		print("\n===================")
	return retval
