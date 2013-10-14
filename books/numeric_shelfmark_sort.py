# -*- coding: utf-8 -*-
"""
# Make a copy of shelfmarks in a form suitable for numerical sorting , e.g. '0010' instead of '10'.
By Sushila Burgess
"""
##=====================================================================================

import sys

input_filename = "/usr/share/mysite/books/sql/shelfmarks_alpha_sort.txt" 
output_filename = "/usr/share/mysite/books/sql/shelfmarks_numeric_sort.sql" 

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
      shelfmark = line_parts[ 1 ].strip()

      print 'Book ID', book_id
      print 'Shelfmark', shelfmark

      update_statement = get_update_statement( book_id, shelfmark )
      print update_statement

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

def get_update_statement( book_id, shelfmark ): #{

  new_value = ''
  numeric_chars = ''
  number_of_digits = 5

  for one_char in shelfmark: #{
    one_char = one_char.strip()

    if one_char == '' or one_char == '.': #{
      one_char = ' '
    #}

    if one_char.isdigit(): #{
      numeric_chars = "%s%s" % (numeric_chars, one_char)
    #}
    else: #{

      if numeric_chars: #{
        numeric_chars = numeric_chars.rjust( number_of_digits, '0' )
        new_value = "%s%s" % (new_value, numeric_chars)
        numeric_chars = ''
      #}

      new_value = "%s%s" % (new_value, one_char)
    #}
  #}

  if numeric_chars: #{ # add any numbers left over at the end
    numeric_chars = numeric_chars.rjust( number_of_digits, '0' )
    new_value = "%s%s" % (new_value, numeric_chars)
    numeric_chars = ''
  #}

  while ' ' + ' ' in new_value: #{  # convert double spaces into single ones
    new_value = new_value.replace( ' ' + ' ', ' ' )
  #}

  new_value = new_value.replace( "'", "''" )  # escape single quotes for SQL input
  new_value = new_value.strip().lower()

  new_value = "update books_book set shelfmark_sort = '%s' where id = %s;" % (new_value, book_id)

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
