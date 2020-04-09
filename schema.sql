create table users (
    id INTEGER primary key autoincrement,
    name text not null,
    email text not null,
    password text not null,
    expert INTEGER not null,
    admin INTEGER not null
);
create table questions (
    id integer primary key autoincrement ,
    question_text text not null ,
    answer_text text,
    asked_by_id integer not null ,
    expert_id integer not null
);