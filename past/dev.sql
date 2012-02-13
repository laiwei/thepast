
DROP TABLE IF EXISTS `task_queue`;
CREATE TABLE `task_queue` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `task_id` int(11) unsigned NOT NULL,
  `task_kind` smallint(4) unsigned NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_time` (`time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='TaskQueue';
