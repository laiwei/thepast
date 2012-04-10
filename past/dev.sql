
DROP TABLE IF EXISTS `confirmation`;

CREATE TABLE `confirmation` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `random_id` varchar(16) NOT NULL, 
  `text` varchar(128) NOT NULL, 
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_idx_random` (`random_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='confirmation';
