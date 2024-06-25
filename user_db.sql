CREATE DATABASE user_db;

USE user_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    mbti VARCHAR(4) NOT NULL
);
insert into `users` values(
	001, 
    "陳俊諺", 
    "410630734@gms.tku.edu.tw",
    'Aa12345678',
    'INFJ'
);
select * from `users`;