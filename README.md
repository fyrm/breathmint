# breathmint
breathmint, A Refreshing Burp Parser

breathmint is a python script that will parse one or more .xml files and produce a spreadsheet (Excel ".xlsx" format) as output. Most of the output generation is done in the other python scripts that breathmint uses: "excelsify.py" and "make_me_pretty.py". By default, there are two worksheets in the workbook output file:
- Burp Issues: results from the Burp xml file(s). One instance per row, which can get lengthy when many apps or paths are identified as vulnerable (ymmv).
- Burp Issues Charts: risk rating listed by ID number (issue #) in column format, which is used as input data to generate a bar chart.

## Prerequisites
breathmint breathmint, excelsify, and make_me_pretty use the following Python modules that are not typically included with the base installation:
- argparse
- xlsxwriter
- bs4
- lxml (required by the bs4 module)

## Usage
The following command line options are supported:
- "-d <directory>" : Location of the directory in which the Burp issues XML files are stored (all .xml files will be opened) and output will be saved
- "-f <filename>" : Name of the single Burp file you want to parse. Ignored if '-d' option is used.
- "-e <exclude_risk_list>" : ('-e <comma,separated,list>') List of risk ratings to exclude from output; partial starting characters accepted; no spaces (default == none excluded).
- "-i <include_risk_list>" : ('-i <comma,separated,list>') List of severity ratings to include in output; partial starting characters accepted; no spaces (default == include all).
- "-o <filename_base>" : Base name of output file to which you want the parsed results to be written; "--parsed--(<YYYYMMDD_HHMM>).xlsx" is added automatically

## Usage Examples
python breathmint.py -d . -o combined_output
python breathmint.py -d ~/Documents/burp/output/ -e info,Low
python breathmint.py -d . -o just_critical_high_medium -i high,MED,cRiTiCaL
python breathmint.py -f some_burp_file.xml -e Informational,Low,Medium -i Critical,High,Medium

## Author
Matthew Flick
