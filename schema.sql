-- MySQL dump 10.13  Distrib 5.7.28, for Linux (x86_64)
--
-- Host: localhost    Database: vizier
-- ------------------------------------------------------
-- Server version	5.7.28-0ubuntu0.19.04.2

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
-- Table structure for table `augs`
--

DROP TABLE IF EXISTS `augs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `augs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) unsigned NOT NULL,
  `locationX` int(11) NOT NULL,
  `locationY` int(11) NOT NULL,
  `comment` varchar(45) DEFAULT NULL,
  `picked_by` bigint(20) DEFAULT NULL,
  `pickupd_comment` varchar(45) DEFAULT NULL,
  `request_time` timestamp NULL DEFAULT NULL,
  `picked_time` timestamp NULL DEFAULT NULL,
  `completed_time` timestamp NULL DEFAULT NULL,
  `guild` bigint(20) unsigned NOT NULL,
  `server` varchar(16) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `augIndex` (`guild`,`server`),
  KEY `augUserIndex` (`guild`,`server`,`user_id`),
  KEY `pickedUserIndex` (`guild`,`server`,`picked_by`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `claims`
--

DROP TABLE IF EXISTS `claims`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `claims` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) unsigned NOT NULL,
  `locationX` int(11) NOT NULL,
  `locationY` int(11) NOT NULL,
  `station_name` varchar(45) DEFAULT NULL,
  `station_comment` varchar(45) DEFAULT NULL,
  `claim_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `guild` bigint(20) unsigned NOT NULL,
  `server` varchar(16) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `claimIndex` (`guild`,`server`,`user_id`),
  KEY `locationIndex` (`guild`,`server`,`locationX`)
) ENGINE=InnoDB AUTO_INCREMENT=112 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fob_history`
--

DROP TABLE IF EXISTS `fob_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fob_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `guild` bigint(20) DEFAULT NULL,
  `server` varchar(16) DEFAULT NULL,
  `fob` bigint(20) DEFAULT NULL,
  `user` bigint(20) DEFAULT NULL,
  `changes` text,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `search` (`guild`,`server`,`fob`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fobs`
--

DROP TABLE IF EXISTS `fobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fobs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `guild` bigint(20) unsigned NOT NULL,
  `server` varchar(16) NOT NULL,
  `name` varchar(45) DEFAULT NULL,
  `locationX` int(11) DEFAULT '0',
  `locationY` int(11) DEFAULT '0',
  `operating` int(10) unsigned DEFAULT '0',
  `destroyer` int(10) unsigned DEFAULT '0',
  `frigate` int(10) unsigned DEFAULT '0',
  `recon` int(10) unsigned DEFAULT '0',
  `gunship` int(10) unsigned DEFAULT '0',
  `trooper` int(10) unsigned DEFAULT '0',
  `carrier` int(10) unsigned DEFAULT '0',
  `dreadnought` int(10) unsigned DEFAULT '0',
  `corvette` int(10) unsigned DEFAULT '0',
  `patrol` int(10) unsigned DEFAULT '0',
  `scout` int(10) unsigned DEFAULT '0',
  `industrial` int(10) unsigned DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `search_index` (`guild`,`server`,`name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `guild` bigint(20) DEFAULT NULL,
  `target` bigint(20) DEFAULT NULL,
  `reference` varchar(45) DEFAULT NULL,
  `value` binary(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `permissionIndex` (`guild`,`target`),
  KEY `permissionUserIndex` (`guild`,`reference`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `settings` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `guild` int(10) unsigned DEFAULT NULL,
  `server` varchar(16) DEFAULT NULL,
  `key` varchar(45) DEFAULT NULL,
  `value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `settingIndex` (`guild`,`server`,`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-09-14 23:12:16
