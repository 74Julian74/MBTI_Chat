create database `MBTI`;
show databases;
use `MBTI`;

create table `使用者帳戶`(
	`UserID` int primary key not null,
	`UserName` varchar(20) not null,
    `Email` varchar(50) not null,
    `Password` varchar(20) not null unique,
    `ProfilePicture` varchar(50),
    `LastActive` date,
    `MBTI` varchar(5),
    `機器人回話type` varchar(20),
    `生日` date not null,
    `年齡` int not null,
    `星座` varchar(3) not null
);#創建資料庫

create table `聊天訊息`(
	`GroupID` int not null,
	`MessageID` int not null,
    `SenderID` int not null,
    `ChatContent` varchar(50)  not null,
    `Timestamp` timestamp not null,
    `情緒欄位` varchar(10) not null,
    PRIMARY KEY (`GroupID`, `MessageID`)
);#創建資料庫

create table `好友關係`(
	`UserID1` int not null,
	`UserID2` int not null,
    `Status` boolean not null,
    `Timestamp` datetime not null,
    PRIMARY KEY (`UserID1`, `UserID2`)
);#創建資料庫

create table `聊天室審核類型`(
	`GroupID` int primary key not null,
	`Filter Type` varchar(10) ,#(色情訊息，廣告，垃圾郵件)
    `Enable` boolean not null
);#創建資料庫

create table `聊天室`(
	`GroupID` int primary key not null,
	`GroupNname` varchar(20),
    `CreatorID` int not null,
    `CreateAt` datetime not null,
    `過濾發言種類` boolean not null
);#創建資料庫

create table `聊天室成員`(
	`GroupID` int primary key not null,
	`UserID` int not null,
    `Role` varchar(10) not null,#(管理員，成員，黑名單)
    `暱稱` varchar(10)
);#創建資料庫

create table `使用者設定`(
	`UserID` int primary key not null,
	`NotificationSound` boolean not null,
    `Theme` blob,
    `Language` varchar(20) not null
);#創建資料庫

create table `通知`(
	`NotificationID` int primary key not null,
	`UserID` int not null,
    `NotificationType` varchar(10) not null,
    `Content` varchar(20) not null,
    `Timestamp` timestamp not null,
    `IsRead` boolean not null
);#創建資料庫

insert into `使用者帳戶` values(
	1, 
    '陳俊諺', 
    '410630734@gms.tku.edu.tw', 
	'Aa12345678',
	"ProfilePicture/下載.jpg",
    '2024-1-12', 
    'INFJ', 
    '開心', 
    '2002-11-19', 
    21, 
	'天蠍座'
);
insert into `使用者帳戶` values(
	2, 
    '陳俊劭', 
    '410630494@gms.tku.edu.tw', 
	'H125827970',
	"ProfilePicture/Peter.png",
    '2024-2-12', 
    'ISFP', 
    '開心', 
    '2003-01-03', 
    21, 
	'摩羯座'
);
insert into `使用者帳戶` values(
	3, 
    '謝程安', 
    'a0903592713@gmail.com', 
	'Jj12345678',
	"ProfilePicture/Steve.png",
    '2024-1-12', 
    'INFP', 
    '憤怒', 
    '2003-07-13', 
    20, 
	'巨蟹座'
);
insert into `使用者帳戶` values(
	4, 
    '張珈豪', 
    '410631450@gms.tku.edu.tw', 
	'Bb12345678',
	"ProfilePicture/Tony.jpg",
    '2024-4-12', 
    'ENTJ', 
    '開心', 
    '2003-03-11', 
    21, 
	'雙魚座'
);
insert into `使用者帳戶` values(
	1, 
    '陳俊諺', 
    '410630734@gms.tku.edu.tw', 
	'Aa12345678',
	"ProfilePicture/Judy.jpg",
    '2024-1-12', 
    'INFJ', 
    '開心', 
    '2002-11-19', 
    21, 
	'天蠍座'
);

insert into `聊天訊息` values(
	1, 
    1, 
    1, 
	"ChatContent/聊天內容.jpg",
    '2024-5-11 19:20:14', 
	'難過'
);
insert into `聊天訊息` values(
	1, 
    1, 
    1, 
	"ChatContent/聊天內容.jpg",
    '2024-5-11 19:20:14', 
	'難過'
);
insert into `聊天訊息` values(
	1, 
    1, 
    1, 
	"ChatContent/聊天內容.jpg",
    '2024-5-11 19:20:14', 
	'難過'
);
insert into `聊天訊息` values(
	1, 
    1, 
    1, 
	"ChatContent/聊天內容.jpg",
    '2024-5-11 19:20:14', 
	'難過'
);
insert into `聊天訊息` values(
	1, 
    1, 
    1, 
	"ChatContent/聊天內容.jpg",
    '2024-5-11 19:20:14', 
	'難過'
);


insert into `聊天室審核類型` values(
	1, 
    "色情訊息", 
    "1"
);
insert into `聊天室審核類型` values(
	2, 
    "廣告", 
    "0"
);
insert into `聊天室審核類型` values(
	3, 
    "垃圾郵件", 
    "1"
);

insert into `聊天室` values(
	1, 
    "Go to play", 
    1,
    '2022-10-10',
    '1'
);
insert into `聊天室` values(
	2, 
    "資管三A", 
    2,
    '2021-7-11',
    '1'
);
insert into `聊天室` values(
	2, 
    "資管三A", 
    2,
    '2021-7-11',
    '1'
);
insert into `聊天室` values(
	3, 
    "專題", 
    1,
    '2023-11-20',
    '0'
);
insert into `聊天室` values(
	4, 
    "資料庫設計", 
    3,
    '2024-5-11',
    '1'
);
insert into `聊天室` values(
	5, 
    "進階程式設計", 
    4,
    '2023-8-12',
    '1'
);
drop table `聊天訊息`;
#丟掉資料庫
select * from `使用者帳戶`;
select * from `聊天訊息`;
select * from `好友關係`;
select * from `聊天室審核類型`;
select * from `聊天室`;
select * from `聊天室成員`;
select * from `使用者設定`;
select * from `通知`;
#取得資料

update `MBTI`
set `major`= "happy"
where `MBTI`= "ENTJ";#更新資料
