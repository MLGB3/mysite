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
  number_of_digits = 4

  roman_dict = { 'vi'  : '0500',
                 'vii' : '0600',
                 'viii': '0700', 
                 'ix'  : '0800', 
                 'x'   : '0900',
                 'xi'  : '1000', 
                 'xii' : '1100', 
                 'xiii': '1200', 
                 'xiv' : '1300', 
                 'xv'  : '1400', 
                 'xvi' : '1500', 
                 'xvii': '1600' }

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

  # Try and set parts of centuries (first quarter, etc)
  date_string = date_string.replace ( ' in', ' 0010 ' )
  date_string = date_string.replace ( 'in.', ' 0010 ' )

  date_string = date_string.replace ( ' 1/4', ' 0025 ' )
  date_string = date_string.replace ( 'i1/4', 'i 0025 ' )

  date_string = date_string.replace ( ' 2/4', ' 0045 ' )
  date_string = date_string.replace ( 'i2/4', 'i 0045 ' )

  date_string = date_string.replace ( 'med.', ' 0050 ' )
  date_string = date_string.replace ( ' med', ' 0050 ' )
  date_string = date_string.replace ( '(med', ' 0050 ' )

  date_string = date_string.replace ( ' 3/4', ' 0075 ' )
  date_string = date_string.replace ( 'i3/4', 'i 0075 ' )
  date_string = date_string.replace ( ' 4/4', ' 0090 ' )
  date_string = date_string.replace ( 'i4/4', 'i 0090 ' )

  date_string = date_string.replace ( 'ex.', ' 0099 ' )
  date_string = date_string.replace ( ' ex', ' 0099 ' )

  # If we replace them in this order, hopefully it will come out right!
  roman_list = [ 'ix', 'xvii', 'xvi', 'xv', 'xiv', 'xiii', 'xii', 'xi', 'x', 'viii', 'vii', 'vi' ]

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

      if numeric_chars: #{
        numeric_chars = numeric_chars.rjust( number_of_digits, '0' )
        new_value = "%s%s | " % (new_value, numeric_chars)
        numeric_chars = ''
      #}

      if one_char == ' ': new_value = "%s%s" % (new_value, one_char)
    #}
  #}

  if numeric_chars: #{ # add any numbers left over at the end
    numeric_chars = numeric_chars.rjust( number_of_digits, '0' )
    new_value = "%s%s | " % (new_value, numeric_chars)
    numeric_chars = ''
  #}

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

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  rewriteDataFile()

##=====================================================================================
