-- MySQL dump 10.13  Distrib 5.1.61, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: thepast
-- ------------------------------------------------------
-- Server version	5.1.61-0+squeeze1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `confirmation`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `confirmation` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `random_id` varchar(16) NOT NULL,
  `text` varchar(128) NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_idx_random` (`random_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 COMMENT='confirmation';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `oauth2_token`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oauth2_token` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `alias_id` int(11) unsigned NOT NULL,
  `access_token` varchar(128) NOT NULL DEFAULT '',
  `refresh_token` varchar(128) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_alias_id` (`alias_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1748 DEFAULT CHARSET=utf8 COMMENT='oauth2_token';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `passwd`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `passwd` (
  `user_id` int(11) unsigned NOT NULL,
  `email` varchar(63) NOT NULL,
  `salt` varchar(8) NOT NULL DEFAULT '',
  `passwd` varchar(15) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uniq_idx_uid` (`user_id`),
  UNIQUE KEY `uniq_idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='passwd';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `status`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `origin_id` varchar(20) NOT NULL DEFAULT '0',
  `create_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `site` varchar(2) NOT NULL,
  `category` smallint(4) NOT NULL,
  `title` varchar(150) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_origin` (`origin_id`,`site`,`category`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_uid` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=32302780 DEFAULT CHARSET=utf8 COMMENT='status';
/*!40101 SET character_set_client = @saved_cs_client */;


create table `note` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `user_id` int(11) unsigned NOT NULL,
    `title` varchar(150) NOT NULL DEFAULT '',
    `content` TEXT NOT NULL DEFAULT '',
    `create_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
    `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON update CURRENT_TIMESTAMP,
    `fmt` varchar(2) NOT NULL DEFAULT 'P',
    `privacy` varchar(2) DEFAULT 'P',
    PRIMARY KEY (`id`),
    KEY `idx_uid` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='note';

--
-- Table structure for table `sync_task`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sync_task` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `category` smallint(4) NOT NULL,
  `user_id` int(11) unsigned NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_user_cate` (`user_id`,`category`)
) ENGINE=InnoDB AUTO_INCREMENT=2214 DEFAULT CHARSET=utf8 COMMENT='sync_task';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `task_queue`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_queue` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `task_id` int(11) unsigned NOT NULL,
  `task_kind` smallint(4) unsigned NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_time` (`time`)
) ENGINE=InnoDB AUTO_INCREMENT=302 DEFAULT CHARSET=utf8 COMMENT='TaskQueue';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` varchar(16) NOT NULL DEFAULT '',
  `name` varchar(63) NOT NULL DEFAULT '',
  `session_id` varchar(16) DEFAULT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_uid` (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=654 DEFAULT CHARSET=utf8 COMMENT='user';
/*!40101 SET character_set_client = @saved_cs_client */;

CREATE TABLE `pdf_settings` (
  `user_id` int(11) unsigned NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='pdf_settings';

--
-- Table structure for table `user_alias`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_alias` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `type` varchar(2) NOT NULL DEFAULT '',
  `user_id` int(11) unsigned NOT NULL DEFAULT '0',
  `alias` varchar(128) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_alias_type` (`alias`,`type`),
  KEY `idx_uid` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1018 DEFAULT CHARSET=utf8 COMMENT='alias';
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

CREATE TABLE `user_tokens` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `token` varchar(64) NOT NULL,
  `device` varchar(128) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_token` (`token`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8 COMMENT='user_tokens';
-- Dump completed on 2012-04-10 23:29:34
