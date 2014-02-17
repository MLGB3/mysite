drop table if exists books_photo;

create table books_photo (
  id        int(11)        not null    auto_increment,
  item_id   int(11)        not null    ,
  title     varchar(100)   not null    ,
  image     varchar(100)   not null    ,
  caption   varchar(250)   not null    ,

  primary key (id )
);

alter table books_photo
add constraint photo_of_book
foreign key ( item_id )
references books_book( id );

insert into books_photo
select * from feeds_photo;

drop table feeds_photo;

create view feeds_photo as select * from books_photo;


