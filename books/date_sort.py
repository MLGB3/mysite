# -*- coding: utf-8 -*-
"""
# Make a copy of dates in a form suitable for numerical sorting , e.g. '1100' instead of 's.xii'.
By Sushila Burgess
"""
##=====================================================================================

import sys

input_filename = "/usr/share/mysite/books/sql/dates_alpha_sort.txt" 
output_filename = "/usr/share/mysite/books/sql/dates_numeric_sort.sql" 

tab = '\t'
newline = '\n'
carriage_return = '\r'

number_of_digits = 4
start_of_century_marker = 9999

##=====================================================================================

def rewriteDataFile(): #{

  #=================================================================
  # Read each line of the original file, manipulate it as necessary,
  # and then write it into the new file.
  #=================================================================
  try:
    infile_handle = file
    outfile_handle = file

    infile_handle = open( input_filename, 'r' )
    outfile_handle = open( output_filename, 'wb' )

    for line_of_file in infile_handle.readlines(): #{

      line_parts = line_of_file.split( tab, 1 )
      if len( line_parts ) != 2: #{
        print 'Invalid line format'
        raise Exception
      #}

      book_id = line_parts[ 0 ]
      date_string = line_parts[ 1 ].strip()

      update_statement = get_update_statement( book_id, date_string )
      sortable_date = update_statement[ len( 'update books_book set date_sort =' ): ]
      sortable_date = sortable_date[ 0 : sortable_date.find( 'where id' ) ]
      print book_id, ':', date_string, '-->', sortable_date
      print ''

      outfile_handle.write( update_statement.encode( 'utf-8' ))
    #}

    outfile_handle.close()
    infile_handle.close()

  except:
    if isinstance( infile_handle, file ):
      if not infile_handle.closed : infile_handle.close()
    if isinstance( outfile_handle, file ):
      if not outfile_handle.closed : outfile_handle.close()
    raise
#}

##=====================================================================================

def get_update_statement( book_id, date_string ): #{

  new_value = ''
  numeric_chars = ''
  step = 0

  roman_dict = { 'vi'  : '0501', # adding 1 will allow 'start of century' values to come first
                 'vii' : '0601',
                 'viii': '0701', 
                 'ix'  : '0801', 
                 'x'   : '0901',
                 'xi'  : '1001', 
                 'xii' : '1101', 
                 'xiii': '1201', 
                 'xiv' : '1301', 
                 'xv'  : '1401', 
                 'xvi' : '1501', 
                 'xvii': '1601' }

  # Get rid of a few strings that might give the wrong result
  date_string = date_string.replace ( '(fols. 1--130)', '' )
  date_string = date_string.replace ( '(fols. 131--179)', '' )
  date_string = date_string.replace ( '(fols. 1--183)', '' )
  date_string = date_string.replace ( '(fols. 184ff.)', '' )
  date_string = date_string.replace ( '(fols. 33r--56r)', '' )
  date_string = date_string.replace ( '(vols. 1--2)', '' )
  date_string = date_string.replace ( '(vol. 3)', '' )
  date_string = date_string.replace ( '(fols. 37--67, 94--101)', '' )
  date_string = date_string.replace ( '(pp. 1--8', '' )
  date_string = date_string.replace ( '(fols. 1--24, 227--229)', '' )
  date_string = date_string.replace ( 'fols. 105--118', '' )
  date_string = date_string.replace ( '(fols. 1--3, 141--152)', '' )

  date_string = date_string.replace ( '1)', '' )
  date_string = date_string.replace ( ' 2)', '' )
  date_string = date_string.replace ( '(2)', '' )
  date_string = date_string.replace ( ' 3)', '' )
  date_string = date_string.replace ( '(3)', '' )
  date_string = date_string.replace ( ' 4)', '' )
  date_string = date_string.replace ( '(4)', '' )

  date_string = date_string.replace ( 'Oxford', '' ) # get rid of words e.g. containing X and VI.
  date_string = date_string.replace ( 'Treviso', '' )
  date_string = date_string.replace ( 'vol', '' )

  date_string = date_string.replace ( ' 11 July', '' )
  date_string = date_string.replace ( '12. Nov.', '' )
  date_string = date_string.replace ( 'GW 2880', '' )

  date_string = date_string.replace ( '1295--96', '1295' )
  date_string = date_string.replace ( '1280--90', '1280' )
  date_string = date_string.replace ( '1497/8', '1497' )
  date_string = date_string.replace ( '1477--78', '1477' )
  date_string = date_string.replace ( '1484--5', '1484' )
  date_string = date_string.replace ( '1201--05', '1201' )
  date_string = date_string.replace ( '1450--60', '1450' )
  date_string = date_string.replace ( '1147--1176', '1147' )
  date_string = date_string.replace ( '1081--1095', '1081' )
  date_string = date_string.replace ( '1088--1093', '1088' )
  date_string = date_string.replace ( '1474--77', '1474' )
  date_string = date_string.replace ( '1493--1494', '1493' )
  date_string = date_string.replace ( '1498--1502', '1498' )
  date_string = date_string.replace ( '1191--1192', '1191' )
  date_string = date_string.replace ( '1430--1460', '1430' )
  date_string = date_string.replace ( '1448--1455', '1448' )
  date_string = date_string.replace ( '1459--1460', '1459' )
  date_string = date_string.replace ( '1340--1350', '1340' )
  date_string = date_string.replace ( '1474--1475', '1474' )
  date_string = date_string.replace ( '1410--1420', '1410' )
  date_string = date_string.replace ( '1472--1473', '1472' )
  date_string = date_string.replace ( '1534--1535', '1534' )
  date_string = date_string.replace ( '1109--1110', '1109' )
  date_string = date_string.replace ( '1302--1303', '1302' )
  date_string = date_string.replace ( '1400--1405', '1400' )
  date_string = date_string.replace ( '1457--1461', '1457' )
  date_string = date_string.replace ( '1460--1461', '1460' )
  date_string = date_string.replace ( '1383--1384', '1383' )

  # Try and set parts of centuries (first quarter, etc)
  # Note: 'in' means '1st half of the century' and 'ex' means 'second half of the century'
  # And so do '1' and '2'.

  # First try and get things into a consistent format
  date_string = date_string.replace ( 'i1/4', 'i FIRSTQUARTER' )
  date_string = date_string.replace ( 'i2/4', 'i SECONDQUARTER' )
  date_string = date_string.replace ( 'i 1/4', 'i FIRSTQUARTER' )
  date_string = date_string.replace ( 'i 2/4', 'i SECONDQUARTER' )

  date_string = date_string.replace ( 'x1/4', 'x FIRSTQUARTER' )
  date_string = date_string.replace ( 'x2/4', 'x SECONDQUARTER' )
  date_string = date_string.replace ( 'x 1/4', 'x FIRSTQUARTER' )
  date_string = date_string.replace ( 'x 2/4', 'x SECONDQUARTER' )

  date_string = date_string.replace ( 'v1/4', 'v FIRSTQUARTER' )
  date_string = date_string.replace ( 'v2/4', 'v SECONDQUARTER' )
  date_string = date_string.replace ( 'v 1/4', 'v FIRSTQUARTER' )
  date_string = date_string.replace ( 'v 2/4', 'v SECONDQUARTER' )

  date_string = date_string.replace ( 'i1', 'i in' )
  date_string = date_string.replace ( 'i2', 'i ex' )
  date_string = date_string.replace ( 'i 1', 'i in' )
  date_string = date_string.replace ( 'i 2', 'i ex' )

  date_string = date_string.replace ( 'x1', 'x in' )
  date_string = date_string.replace ( 'x2', 'x ex' )
  date_string = date_string.replace ( 'x 1', 'x in' )
  date_string = date_string.replace ( 'x 2', 'x ex' )

  date_string = date_string.replace ( 'v1', 'v in' )
  date_string = date_string.replace ( 'v2', 'v ex' )
  date_string = date_string.replace ( 'v 1', 'v in' )
  date_string = date_string.replace ( 'v 2', 'v ex' )

  date_string = date_string.replace( 'FIRSTQUARTER', ' 1/4 ' )
  date_string = date_string.replace( 'SECONDQUARTER', ' 2/4 ' )

  #============================
  # Now change words to numbers
  #============================

  # First quarter of century
  date_string = date_string.replace ( ' 1/4', ' %s ' % start_of_century_marker  )  # to be replaced later

  # First half of century
  date_string = date_string.replace ( ' in', ' %s ' % start_of_century_marker )
  date_string = date_string.replace ( 'in.', ' %s ' % start_of_century_marker )


  # Second quarter of century
  date_string = date_string.replace ( ' 2/4', ' 26 ' )
  date_string = date_string.replace ( 'i2/4', 'i 26 ' )

  # Middle of century
  date_string = date_string.replace ( 'med.', ' 50 ' )
  date_string = date_string.replace ( ' med', ' 50 ' )
  date_string = date_string.replace ( '(med', ' 50 ' )

  # Second half of century
  date_string = date_string.replace ( 'ex.', ' 51 ' )
  date_string = date_string.replace ( ' ex', ' 51 ' )

  # Third quarter of century
  date_string = date_string.replace ( ' 3/4', ' 52 ' )
  date_string = date_string.replace ( 'i3/4', 'i 52 ' )

  # Fourth quarter of century
  date_string = date_string.replace ( ' 4/4', ' 76 ' )
  date_string = date_string.replace ( 'i4/4', 'i 76 ' )


  # If we replace them in this order, hopefully it will come out right!
  roman_list = [ 'ix', 'xvii', 'xvi', 'xv', 'xiv', 'xiii', 'xii', 'xi', 'x', 'viii', 'vii', 'vi' ]

  # First make all the dates the same case (lower case)
  for roman_numeral in roman_list: #{
    upper_numeral = roman_numeral.upper()
    if upper_numeral in date_string: #{
      date_string = date_string.replace( upper_numeral, roman_numeral )
    #}
  #}

  # Now, actually convert Roman numerals to modern numbers
  for roman_numeral in roman_list: #{
    if roman_numeral in date_string: #{
      if roman_dict.has_key( roman_numeral ): #{
        year = roman_dict[ roman_numeral ]
        date_string = date_string.replace( roman_numeral, year )
      #}
    #}
  #}

  for one_char in date_string: #{
    one_char = one_char.strip()

    if one_char == '' or one_char == '-' or one_char == '/': #{
      one_char = ' '
    #}

    if one_char.isdigit(): #{
      numeric_chars = "%s%s" % (numeric_chars, one_char)
    #}
    else: #{
      new_value, numeric_chars, step = finish_processing_number( new_value, numeric_chars, step )
      if one_char == ' ': new_value = "%s%s" % (new_value, one_char)
    #}
  #}

  new_value, numeric_chars, step = finish_processing_number( new_value, numeric_chars, step )

  while ' ' + ' ' in new_value: #{  # convert double spaces into single ones
    new_value = new_value.replace( ' ' + ' ', ' ' )
  #}

  # However, we may want to add back some double spaces in order to sort the dates of style
  # 's. xiii in.' - i.e. START of the 13th century - before those that are given JUST as 13th century.
  if '00 | 001' in new_value:
    new_value = new_value.replace( '00 | 001', '00  001' )

  new_value = new_value.replace( "'", "''" )  # escape single quotes for SQL input
  new_value = new_value.strip().lower()

  new_value = "update books_book set date_sort = '%s' where id = %s;" % (new_value, book_id)

  new_value += newline
  return new_value
#}

##=====================================================================================
def finish_processing_number( value, numeric_chars, step ): #{

  if numeric_chars: #{
    step += 1

    print "'%s'" % value
    print numeric_chars

    value = value.strip()
    if value.isdigit():
      intval = int( value )
    else:
      intval = 0
    number = int( numeric_chars )

    if step == 1: #{
      value = numeric_chars.rjust( number_of_digits, '0' )
    #}

    elif step == 2 and (number < 100 or number == start_of_century_marker): #{
      if number == start_of_century_marker:
        new_number = intval - 1
      else:
        new_number = intval + number
      value = "%d" % new_number
      value = value.rjust( number_of_digits, '0' )
    #}

    elif step == 2 and intval > 500 and number >= intval+100: #{
      value = "%s99%d" % (value[ 0:2 ], number)
    #}

    else: #{
      numeric_chars = numeric_chars.rjust( number_of_digits, '0' )
      value = "%s%s | " % (value, numeric_chars)
    #}
    numeric_chars = ''
  #}

  return value, numeric_chars, step
#}
##=====================================================================================

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  rewriteDataFile()

##=====================================================================================
