
DROP TABLE IF EXISTS `passwd`;
CREATE TABLE `passwd` (
  `user_id` int(11) unsigned NOT NULL,
  `email` varchar(63) NOT NULL,
  `salt` varchar(8) NOT NULL DEFAULT '',
  `passwd` varchar(15) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uniq_idx_uid` (`user_id`),
  UNIQUE KEY `uniq_idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='passwd';
