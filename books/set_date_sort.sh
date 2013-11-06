#! /bin/bash
# Make a copy of dates in a form suitable for numerical sorting , e.g. '1100' instead of 's.xii'.

pw=$1
if [ "$pw" = "" ]
then
  echo 'Password must be passed in as first parameter.'
  exit
fi

cd /usr/share/mysite/books

mysql -umlgbAdmin -p"$pw" mlgb --skip-column-names > sql/dates_alpha_sort.txt <<EndOfSQLStatement
  select id, coalesce( date, '' )
  from books_book
  order by date, id;
EndOfSQLStatement

python date_sort.py  # creates file sql/dates_numeric_sort.sql

mysql -umlgbAdmin -p"$pw" mlgb <  sql/dates_numeric_sort.sql

