#! /bin/bash
# Make a copy of shelfmarks in a form suitable for numerical sorting , e.g. '0010' instead of '10'.

pw=$1
if [ "$pw" = "" ]
then
  echo 'Password must be passed in as first parameter.'
  exit
fi

cd /usr/share/mysite/books

mysql -umlgbAdmin -p"$pw" mlgb --skip-column-names > sql/shelfmarks_alpha_sort.txt <<EndOfSQLStatement
  select id, coalesce( shelfmark_1, '' ), ' ', coalesce( shelfmark_2, '' )
  from books_book
  order by id;
EndOfSQLStatement

python numeric_shelfmark_sort.py  # creates file sql/shelfmarks_numeric_sort.sql

mysql -umlgbAdmin -p"$pw" mlgb <  sql/shelfmarks_numeric_sort.sql

