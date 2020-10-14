#!/usr/bin/python3
'''
excelsify
	Write stuff to an Excel spreadsheet
'''

#
#
# -- import public modules --
#
#
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import argparse
import os
import datetime
import traceback
import sys
import re

#
#
# -- import private modules --
#
#
import make_me_pretty

#
#
# -- Global variables --
#
#
SORT_ORDER_RISK = {"Critical":0, "High":1, "Medium":2, "Low":3, "Informational":4}
SORT_ORDER_RISK_ORDERED = ["Critical", "High", "Medium", "Low", "Informational"]
COLUMN_WIDTH_MIN = 10
COLUMN_WIDTH_MAX = 50
COLUMN_WIDTH_START = 20
FILENAME_DEFAULT = "excelsify-output--parsed--" + datetime.datetime.now().strftime('%Y%m%d_%H%M') + ".xlsx"
WB_FONTS = {}
WB_FONTS['header'] = ""
WB_FONTS['center'] = ""
WB_FONTS['left'] = ""
WB_FONTS['red'] = ""
WB_FONTS['date'] = ""
WB_FONTS['total'] = ""
FONT_DEFAULT = 'left'
FONT_SELECTION_BY_NAME = {}
FONT_SELECTION_BY_NAME['center'] = ["URI", "IP", "Port", "Path", "Location", "Vulnerability Name", "Risk", "Severity", "Confidence"]
FONT_SELECTION_BY_NAME['left'] = ["Target", "Background", "Remediation", "References", "Classification", "Target Details", "Issue Details"]

#
#
# -- Function declarations --
#
#

#
#
#	determine_content_length_min
#
#		determine the minimum length of the content written in the relevant cell
#
#
def determine_content_length_min(content):
	retval_content_length_min = COLUMN_WIDTH_START
	try:
		if isinstance(content, list):
			for content_list_item in content:
				retval_content_length_min = min(retval_content_length_min, determine_content_length_min(content=content_list_item))
		elif isinstance(content, dict):
			for key,val in content.items():
				retval_content_length_min = min(retval_content_length_min, determine_content_length_min(content=key))
				retval_content_length_min = min(retval_content_length_min, determine_content_length_min(content=val))
		else:
			retval_content_length_min = min(retval_content_length_min, len(content))
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.determine_content_length_min()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return retval_content_length_min


#
#
#	determine_content_length_max
#
#		determine the maximum length of the content written in the relevant cell
#
#
def determine_content_length_max(content):
	retval_content_length_max = COLUMN_WIDTH_START
	try:
		if isinstance(content, list):
			for content_list_item in content:
				retval_content_length_max = max(retval_content_length_max, determine_content_length_max(content=content_list_item))
		elif isinstance(content, dict):
			for key,val in content.items():
				retval_content_length_max = max(retval_content_length_max, determine_content_length_max(content=key))
				retval_content_length_max = max(retval_content_length_max, determine_content_length_max(content=val))
		else:
			retval_content_length_max = max(retval_content_length_max, len(content))
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.determine_content_length_max()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return retval_content_length_max


#
#
#	determine_column_width
#
#		determine the appropriate column width based on the minimum and maximum lengths of the content written in the relevant cell
#
#
def determine_column_width(content_length_min, content_length_max):
	retval_column_width = COLUMN_WIDTH_START
	try:
		if (content_length_min >= COLUMN_WIDTH_MAX or content_length_max >= COLUMN_WIDTH_MAX):
			retval_column_width = COLUMN_WIDTH_MAX
		elif content_length_max <= COLUMN_WIDTH_MIN:
			retval_column_width = COLUMN_WIDTH_MIN
		elif (content_length_min > COLUMN_WIDTH_MIN and content_length_max < COLUMN_WIDTH_MAX):
			retval_column_width = int((content_length_min + content_length_max) / 2)
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.determine_column_width()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return retval_column_width


#
#
#	determine_cell_font
#
#		determine the appropriate font to be applied to the relevant cell
#
#
def determine_cell_font(field_name):
	retval_cell_font = FONT_DEFAULT
	try:
		for key,val in FONT_SELECTION_BY_NAME.items():
			if field_name in val:
				retval_cell_font = key
				break
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.determine_cell_font()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return retval_cell_font


#
#
#	prep_workbook
#
#		prepare the results workbook with formatting stuff
#
#
def prep_workbook(workbook):
	try:
		workbook.set_size(2400, 1350)
		WB_FONTS['header'] = workbook.add_format({'bold': True})
		WB_FONTS['header'].set_bg_color('#336699')
		WB_FONTS['header'].set_font_color('#FFFFFF')
		WB_FONTS['header'].set_align('center')
		WB_FONTS['header'].set_align('top')
		WB_FONTS['header'].set_text_wrap()
		WB_FONTS['header'].set_border()
		WB_FONTS['header'].set_font_size(12)
		WB_FONTS['center'] = workbook.add_format()
		WB_FONTS['center'].set_align('center')
		WB_FONTS['center'].set_align('top')
		WB_FONTS['center'].set_text_wrap()
		WB_FONTS['center'].set_border()
		WB_FONTS['left'] = workbook.add_format()
		WB_FONTS['left'].set_align('top')
		WB_FONTS['left'].set_text_wrap()
		WB_FONTS['left'].set_border()
		WB_FONTS['red'] = workbook.add_format()
		WB_FONTS['red'].set_align('center')
		WB_FONTS['red'].set_align('top')
		WB_FONTS['red'].set_text_wrap()
		WB_FONTS['red'].set_font_color('#FF0000')
		WB_FONTS['red'].set_border()
		WB_FONTS['date'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
		WB_FONTS['date'].set_align('center')
		WB_FONTS['date'].set_align('top')
		WB_FONTS['date'].set_text_wrap()
		WB_FONTS['date'].set_border()
		WB_FONTS['total'] = workbook.add_format({'bold': True})
		WB_FONTS['total'].set_bg_color('#BFBFBF')
		WB_FONTS['total'].set_align('center')
		WB_FONTS['total'].set_align('top')
		WB_FONTS['total'].set_text_wrap()
		WB_FONTS['total'].set_border()
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.prep_workbook()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return workbook


#
#
#	set_worksheet_formatting
#
#		prepare a results worksheet
#
#		parameters
#			worksheet_this - the worksheet to which you want the chart added
#			column_data - dictionary with column names as keys and a column details dictionary as values
#							although [currently] the only thing in the column details is the desired column number (order)
#							left as a placeholder in case more interesting things are added later
#			column_content_length - dictionary with column names as keys and min/max length of the content dictionary as values
#							min & max content length values used as input to determine_column_width function
#
#		returns:
#			worksheet_this
#
#
def set_worksheet_formatting(worksheet_this, column_data, column_content_length):
	try:
		for column_name,column_details in column_data.items():
			column_width = determine_column_width(content_length_min=column_content_length[column_name]['min'], content_length_max=column_content_length[column_name]['max'])
			if column_width < COLUMN_WIDTH_MIN:
				column_width = COLUMN_WIDTH_MIN
			elif column_width > COLUMN_WIDTH_MAX:
				column_width = COLUMN_WIDTH_MAX
			if column_width < len(column_name):
				column_width = len(column_name)
			worksheet_this.set_column(column_details['column_number'], column_details['column_number'], column_width)
			worksheet_this.write(0, column_details['column_number'], column_name, WB_FONTS['header'])
		worksheet_this.freeze_panes(1, 0)
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.set_worksheet_formatting()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return worksheet_this


#
#
#	add_chart_worksheet
#
#		adds content and a chart displaying the number of issues by risk rating
#
#		parameters
#			workbook_this - this workbook (is this not obvious?)
#			worksheet_this - the worksheet to which you want the chart added
#			worksheet_name - seriously these are very obvious names
#			issue_risk_rating_list - list of (ordered) risk ratings, which should correspond to the order of issues
#
#		returns:
#			worksheet_this
#
#
def add_chart_worksheet(workbook_this, worksheet_this, worksheet_name, issue_risk_rating_list):
	try:
		num_issues = len(issue_risk_rating_list)
		worksheet_this.set_column(0, 0, 12)
		worksheet_this.set_column(1, 1, 12)
		worksheet_this.write(0, 0, "Risk Rating", WB_FONTS['header'])
		worksheet_this.write(0, 1, "Count", WB_FONTS['header'])
		risk_rating_names = list(SORT_ORDER_RISK.keys())
		risk_rating_names.sort(key=lambda k: SORT_ORDER_RISK[k])
		risk_rating_names.append('Closed')
		row_num = 1
		for i in range(len(risk_rating_names)):
			row_num = 1+i
			worksheet_this.write(row_num, 0, risk_rating_names[i], WB_FONTS['left'])
			abs_cell_ref = xl_rowcol_to_cell(row_num, 0)
			worksheet_this.write_formula(row_num, 1, '=COUNTIF(B$21:B$' + str(num_issues+21) + ', ' + abs_cell_ref + ')', WB_FONTS['left'])
		row_num += 1
		#	total
		worksheet_this.write(row_num, 0, "Total", WB_FONTS['total'])
		worksheet_this.write(row_num+1, 0, "Total Open", WB_FONTS['total'])
		abs_cell_ref_start = xl_rowcol_to_cell(1, 1)
		abs_cell_ref_end = xl_rowcol_to_cell(row_num-1, 1)
		abs_cell_ref_end_open = xl_rowcol_to_cell(row_num-2, 1)
		worksheet_this.write_formula(row_num, 1, '=SUM(' + abs_cell_ref_start + ":" + abs_cell_ref_end + ')', WB_FONTS['total'])
		#	total open
		row_num += 1
		worksheet_this.write_formula(row_num, 1, '=SUM(' + abs_cell_ref_start + ":" + abs_cell_ref_end_open + ')', WB_FONTS['total'])
		#	write out risk rating for each issue starting in row 20 (headings) and row 21 (entries)
		worksheet_this.write(20, 0, "ID", WB_FONTS['header'])
		worksheet_this.write(20, 1, "Risk Level", WB_FONTS['header'])
		row_num = 21
		for i in range(len(issue_risk_rating_list)):
			worksheet_this.write(row_num, 0, str(i+1), WB_FONTS['left'])
			worksheet_this.write(row_num, 1, str(issue_risk_rating_list[i]), WB_FONTS['left'])
			row_num += 1
		#	chart
		chart = workbook_this.add_chart({'type': 'column', 'name':'Number of Vulnerabilities by Risk Rating'})
		chart_data_cat_start = xl_rowcol_to_cell(1, 0, row_abs=True, col_abs=True)
		chart_data_cat_end = xl_rowcol_to_cell(len(risk_rating_names), 0, row_abs=True, col_abs=True)
		chart_color_list = []
		chart_color_list.append("#7030A0")	# Critical -> Purple
		chart_color_list.append("#FF0000")	# High -> Red
		chart_color_list.append("#ED7D31")	# Medium -> Orange
		chart_color_list.append("#0070C0")	# Low -> Blue
		chart_color_list.append("#00B050")	# Informational -> Green
		chart_color_list.append("#808080")	# Closed -> Grey
		for chart_row_num in range(1, 1+len(risk_rating_names)):
			chart_data_values = xl_rowcol_to_cell(chart_row_num, 1, row_abs=True, col_abs=True)
			#	'values', 'categories' : [sheetname, first_row, first_col, last_row, last_col]
			chart.add_series({
				'name':risk_rating_names[chart_row_num-1],
				'categories':['\''+worksheet_name+'\'', chart_row_num, 0, chart_row_num, 0],
				'values':['\''+worksheet_name+'\'', chart_row_num, 1, chart_row_num, 1],
				'fill':{'color':chart_color_list[chart_row_num-1]},
				'border':{'color':'black'},
				'data_labels':{'value':True, 'font':{'size':16}},
				'gap':100
			})
		chart.set_title({'name':"Vulnerabilities by Risk Rating", 'position':'center', 'name_font':{'size':28, 'bold':True}})
		chart.set_x_axis({'visible': False})
		chart.set_legend({'font':{'bold':1, 'italic':1, 'size':16}})
		worksheet_this.insert_chart('F2', chart, {'x_scale': 2, 'y_scale': 2})
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.add_chart_worksheet()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return worksheet_this


#
#
#	create_worksheet_data
#
#		create data dictionary for output
#
#		parameters:
#			output_column_names - list of column names to include in the desired worksheet
#				column names must be keys in each issue data dictionary in issue_data_list
#			issue_data_list - list of issue data dictionaries
#
#		returns:
#			worksheet_data dictionary that can be used as a parameter in the create_workbook function
#
#
def create_worksheet_data(output_column_names, issue_data_list):
	try:
		excelsify_worksheet_data = {}
		excelsify_worksheet_data['add_charts'] = True
		excelsify_worksheet_data['row_data'] = []
		for issue_data in issue_data_list:
			new_row_data = {}
			for column_name in output_column_names:
				if not column_name in issue_data.keys():
					print("excelsify.create_worksheet_data: column_name (" + column_name + ") is not a valid key in this issue_data dictionary:\n", issue_data)
				elif column_name == 'Target':
					#
					#	example for handling a 'Target' dictionary with risk ratings as keys and each corresponding value being a list of target dictionaries
					#		revise as needed depending on how you define an optional/added 'Target' field for each issue
					#	could also use this as an example for handling other types of issue data storage
					target_pretty = """"""
					if isinstance(issue_data[column_name], dict):
						num_risk_ratings = len(issue_data[column_name].keys())
						for risk_rating in SORT_ORDER_RISK_ORDERED:
							if risk_rating in issue_data[column_name].keys():
								if num_risk_ratings > 1:
									target_pretty += risk_rating + """\n"""
								#
								#	could add some logic here to change include_details to True based on certain data/requirements
								for target_dict in issue_data[column_name][risk_rating]:
									temp = make_me_pretty.target_pretty(target_dict=target_dict, include_details=False, details_separator="\n")
									if not temp in target_pretty:
										target_pretty += temp + """\n"""
					else:
						print("\n\n\n excelsify.create_worksheet_data: uh, this probably should not happen \n\n\n")
						target_pretty = str(issue_data[column_name])
					new_row_data[column_name] = target_pretty
				else:
					new_row_data[column_name] = issue_data[column_name]
			excelsify_worksheet_data['row_data'].append(new_row_data)
		excelsify_worksheet_data['column_data'] = {}
		column_number = 0
		for column_name in output_column_names:
			excelsify_worksheet_data['column_data'][column_name] = {}
			excelsify_worksheet_data['column_data'][column_name]['column_number'] = column_number
			column_number += 1
		return excelsify_worksheet_data
	except Exception as e:
		print("===================")
		print("Exception: excelsify.create_worksheet_data: ")
		print(e)
		traceback.print_exc()
		print("===================")
		return {}


#
#
#	create_workbook
#
#		creates a workbook using the given column/cell formatting and data parameters
#
#		parameters:
#			worksheet_data - output from the create_worksheet_data function
#
#		returns:
#			True|False
#
#
def create_workbook(worksheet_data, out_filename=FILENAME_DEFAULT):
	retval = False
	try:
		workbook = xlsxwriter.Workbook(out_filename, {'strings_to_urls': False})
		workbook = prep_workbook(workbook=workbook)
		for worksheet_name in worksheet_data.keys():
			column_content_length = {}
			issue_risk_rating_list = []
			worksheet_this = workbook.add_worksheet(worksheet_name)
			for column_name in worksheet_data[worksheet_name]['column_data'].keys():
				column_content_length[column_name] = {'min':COLUMN_WIDTH_START, 'max':COLUMN_WIDTH_START}
			row_number = 1
			for row in worksheet_data[worksheet_name]['row_data']:
				for column_name,cell_value in row.items():
					if column_name == "Risk":
						issue_risk_rating_list.append(cell_value)
					column_number = worksheet_data[worksheet_name]['column_data'][column_name]['column_number']
					cell_font = determine_cell_font(field_name=column_name)
					safe_string = make_me_pretty.safe_to_write_string(contents=cell_value)
					safe_string = make_me_pretty.remove_lxml_markup(contents=safe_string)
					safe_string = make_me_pretty.fix_spacing_issues(contents=safe_string)
					if safe_string.endswith("""\n"""):
						safe_string = safe_string[:-1]
					#	reference: ws.write(row_number, column_number, contents, cell_font)
					worksheet_this.write(row_number, column_number, safe_string, WB_FONTS[cell_font])
					column_content_length[column_name]['min'] = min(column_content_length[column_name]['min'], determine_content_length_min(content=safe_string))
					column_content_length[column_name]['max'] = max(column_content_length[column_name]['max'], determine_content_length_max(content=safe_string))
				row_number += 1
			worksheet_this = set_worksheet_formatting(worksheet_this=worksheet_this, column_data=worksheet_data[worksheet_name]['column_data'], column_content_length=column_content_length)
			if worksheet_data[worksheet_name]['add_charts'] == True:
				chart_worksheet_name = worksheet_name + " Charts"
				chart_worksheet_this = workbook.add_worksheet(chart_worksheet_name)
				chart_worksheet_this = add_chart_worksheet(workbook_this=workbook, worksheet_this=chart_worksheet_this, worksheet_name=chart_worksheet_name, issue_risk_rating_list=issue_risk_rating_list)
		workbook.close()
		retval = True
	except Exception as e:
		print("\n==== Exception ====\n  excelsify.create_workbook()\n----")
		print(e)
		traceback.print_exc()
		print("\n===================")
	return retval
