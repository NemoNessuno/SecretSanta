drop table if exists user;
drop table if exists contributions;
create table user (
    id integer primary key autoincrement,
    user_id text not null, 
    pw_hash text not null, 
    participate integer,
    trait1 text, 
    trait2 text, 
    trait3 text,                           
    trait4 text, 
    trait5 text
);
create table contributions (
    id integer primary key autoincrement,
    description text not null,
    user_id text
);
