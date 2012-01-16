drop database if exists `thepast`;
create database `thepast`;

use `thepast`;

drop table if exists `status`;
CREATE TABLE `status` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `origin_id` int(11) unsigned NOT NULL DEFAULT '0',
  `create_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `site` varchar(2) NOT NULL,
  `category` smallint(4) NOT NULL,
  `title` varchar(300) CHARACTER SET ucs2 NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_origin` (`origin_id`, `site`, `category`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='status';

drop table if exists `user`;
CREATE TABLE `user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` varchar(16) NOT NULL DEFAULT '',
  `name` varchar(63) CHARACTER SET ucs2 NOT NULL DEFAULT '',
  `session_id` varchar(16) DEFAULT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_uid` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='user';


drop table if exists `user_alias`;
CREATE TABLE `user_alias` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `type` varchar(2) NOT NULL DEFAULT '',
  `user_id` int(11) unsigned NOT NULL DEFAULT '0',
  `alias` varchar(63) CHARACTER SET ucs2 NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_alias_type` (`alias`,`type`),
  KEY `idx_uid` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='alias';


drop table if exists `passwd`;
CREATE TABLE `passwd` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `salt` varchar(8) NOT NULL DEFAULT '',
  `passwd` varchar(15) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_uid` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='passwd';

drop table if exists `oauth2_token`;
CREATE TABLE `oauth2_token` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `alias_id` int(11) unsigned NOT NULL,
  `access_token` varchar(128) NOT NULL DEFAULT '',
  `refresh_token` varchar(128) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_alias_id` (`alias_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='oauth2_token';



drop table if exists `sync_task`;
CREATE TABLE `sync_task` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `category` smallint(4) NOT NULL,
  `user_id` int(11) unsigned NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_user_cate` (`user_id`, `category`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='sync_task';


