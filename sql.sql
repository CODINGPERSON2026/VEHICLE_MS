-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: vehicle_management
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `anpr_events`
--

DROP TABLE IF EXISTS `anpr_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `anpr_events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `camera_id` int DEFAULT NULL,
  `captured_plate` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `confidence` float NOT NULL,
  `matched_vehicle_id` int DEFAULT NULL,
  `rfid_event_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `verification_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `snapshot_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_demo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `camera_id` (`camera_id`),
  KEY `matched_vehicle_id` (`matched_vehicle_id`),
  KEY `ix_anpr_events_rfid_event_id` (`rfid_event_id`),
  KEY `ix_anpr_events_timestamp` (`timestamp`),
  KEY `ix_anpr_events_captured_plate` (`captured_plate`),
  CONSTRAINT `anpr_events_ibfk_1` FOREIGN KEY (`camera_id`) REFERENCES `camera_configs` (`id`),
  CONSTRAINT `anpr_events_ibfk_2` FOREIGN KEY (`matched_vehicle_id`) REFERENCES `vehicles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anpr_events`
--

LOCK TABLES `anpr_events` WRITE;
/*!40000 ALTER TABLE `anpr_events` DISABLE KEYS */;
INSERT INTO `anpr_events` VALUES (1,'2026-10-04 06:49:00',NULL,'MH503502',95.5,NULL,NULL,'MATCH',NULL,1);
/*!40000 ALTER TABLE `anpr_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `user_id` int DEFAULT NULL,
  `username` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `related_vehicle` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `related_device` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_audit_logs_timestamp` (`timestamp`),
  KEY `ix_audit_logs_action` (`action`),
  KEY `ix_audit_logs_user_id` (`user_id`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=187 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,'2026-10-03 13:04:21',1,'tiger','LOGIN',NULL,NULL,'Initial Admin account created: \'tiger\'','127.0.0.1'),(2,'2026-10-03 14:00:23',1,'tiger','VEHICLE_CREATE','24BH9074C',NULL,'Created vehicle \'24BH9074C\' (Car, Status: AUTHORIZED)','127.0.0.1'),(3,'2026-10-03 14:09:06',1,'tiger','RFID_ASSIGN','24BH9074C',NULL,'Registered & assigned RFID \'52932A5C\' to vehicle \'24BH9074C\'','127.0.0.1'),(4,'2026-10-03 14:10:11',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.93'),(5,'2026-10-03 14:11:52',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL EXIT recorded for \'24BH9074C\' by tiger. Duration: 1m 40s. Reason: Operator processed manual exit','127.0.0.1'),(6,'2026-10-03 14:13:28',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.93'),(7,'2026-10-03 14:14:55',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-03 14:13:27','192.168.137.93'),(8,'2026-10-03 14:15:42',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL EXIT recorded for \'24BH9074C\' by tiger. Duration: 2m 14s. Reason: Operator processed manual exit','127.0.0.1'),(9,'2026-10-03 14:15:51',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.93'),(10,'2026-10-03 14:16:59',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-03 14:15:51','192.168.137.93'),(11,'2026-10-03 14:17:21',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL EXIT recorded for \'24BH9074C\' by tiger. Duration: 1m 29s. Reason: Operator processed manual exit','127.0.0.1'),(12,'2026-10-03 14:22:00',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.93'),(13,'2026-10-03 14:22:27',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-03 14:21:59','192.168.137.93'),(14,'2026-10-03 14:23:09',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-03 14:21:59','192.168.137.93'),(15,'2026-10-03 14:23:18',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-03 14:21:59','192.168.137.93'),(16,'2026-10-04 06:08:21',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(17,'2026-10-04 06:09:20',1,'tiger','RFID_DEACTIVATE','24BH9074C',NULL,'Unassigned RFID \'52932A5C\' from vehicle \'24BH9074C\'','127.0.0.1'),(18,'2026-10-04 06:11:08',1,'tiger','VEHICLE_CREATE','MH503502',NULL,'Created vehicle \'MH503502\' (Motorcycle, Status: AUTHORIZED)','127.0.0.1'),(19,'2026-10-04 06:15:59',1,'tiger','RFID_ASSIGN','MH503502',NULL,'Assigned RFID \'52932A5C\' to vehicle \'MH503502\'','127.0.0.1'),(20,'2026-10-04 06:16:40',1,'tiger','RFID_REASSIGN','MH503502',NULL,'Assigned RFID \'52932A5C\' to vehicle \'MH503502\'','127.0.0.1'),(21,'2026-10-04 06:24:45',1,'tiger','VEHICLE_DEACTIVATE','24BH9074C',NULL,'Permanently deleted vehicle \'24BH9074C\'','127.0.0.1'),(22,'2026-10-04 06:46:09',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.9'),(23,'2026-10-04 06:46:48',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 38s. Reason: Operator processed manual exit','127.0.0.1'),(24,'2026-10-04 06:49:00',1,'tiger','CAMERA_CONFIG','MH503502',NULL,'ANPR Event: Plate \'MH503502\' (95.5%) -> MATCH','127.0.0.1'),(25,'2026-10-04 07:23:15',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.9'),(26,'2026-10-04 07:45:57',NULL,'SYSTEM','DENIED_ATTEMPT','MH503502','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'MH503502\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-04 07:23:14','192.168.137.9'),(27,'2026-10-04 07:49:08',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 25m 53s. Reason: Operator processed manual exit','127.0.0.1'),(28,'2026-10-04 12:18:17',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(29,'2026-10-04 12:23:19',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.7'),(30,'2026-10-04 12:24:16',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 56s. Reason: Operator processed manual exit','127.0.0.1'),(31,'2026-10-04 12:56:39',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.7'),(32,'2026-10-04 12:59:40',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 3m 0s. Reason: Operator processed manual exit','127.0.0.1'),(33,'2026-10-04 12:59:44',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.7'),(34,'2026-10-04 13:06:42',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 6m 57s. Reason: Operator processed manual exit','127.0.0.1'),(35,'2026-10-04 13:06:52',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.7'),(36,'2026-10-04 13:07:25',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 32s. Reason: Operator processed manual exit','127.0.0.1'),(37,'2026-10-04 13:07:41',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.7'),(38,'2026-10-04 13:08:15',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 33s. Reason: Operator processed manual exit','127.0.0.1'),(39,'2026-10-04 13:11:45',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.7'),(40,'2026-10-04 13:12:22',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 37s. Reason: Operator processed manual exit','127.0.0.1'),(41,'2026-10-04 13:52:31',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL ENTRY recorded for \'MH503502\' by tiger. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(42,'2026-10-04 14:07:25',NULL,'SYSTEM','VEHICLE_ENTRY','MH503502','GATE01','Authorized ENTRY for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','192.168.137.7'),(43,'2026-10-04 14:08:53',1,'tiger','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL EXIT recorded for \'MH503502\' by tiger. Duration: 1m 27s. Reason: Operator processed manual exit','127.0.0.1'),(44,'2026-10-04 14:23:56',NULL,'SYSTEM','VEHICLE_EXIT','MH503502','GATE01','Authorized EXIT (Outbound) for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(45,'2026-10-04 14:24:41',NULL,'SYSTEM','VEHICLE_EXIT','MH503502','GATE01','Authorized EXIT (Outbound) for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(46,'2026-10-04 14:35:19',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'ED1\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','127.0.0.1'),(47,'2026-10-04 14:35:19',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'ED1\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','127.0.0.1'),(48,'2026-10-04 14:39:48',NULL,'SYSTEM','VEHICLE_EXIT','MH503502','GATE01','Authorized EXIT (Outbound Dispatch) for MH503502 (Motorcycle) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(49,'2026-10-04 14:39:48',NULL,'SYSTEM','MANUAL_OVERRIDE','MH503502',NULL,'MANUAL RETURN (IN Depot) recorded for \'MH503502\' by Operator. Trip Duration: 0s. Reason: Vehicle returned to depot','127.0.0.1'),(50,'2026-10-04 14:42:14',1,'tiger','VEHICLE_DEACTIVATE','MH503502',NULL,'Permanently deleted vehicle \'MH503502\'','127.0.0.1'),(51,'2026-10-04 14:45:34',1,'tiger','VEHICLE_CREATE','24BH9074C',NULL,'Created vehicle \'24BH9074C\' (Car, Status: AUTHORIZED)','127.0.0.1'),(52,'2026-10-04 14:46:23',1,'tiger','RFID_ASSIGN','24BH9074C',NULL,'Assigned RFID \'52932A5C\' to vehicle \'24BH9074C\'','127.0.0.1'),(53,'2026-10-04 14:46:36',1,'tiger','RFID_DEACTIVATE',NULL,NULL,'Deleted RFID Card \'TESTDUP1\'','127.0.0.1'),(54,'2026-10-04 14:50:49',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(55,'2026-10-04 14:52:06',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED EXIT for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already outside on trip since 2026-10-04 14:50:49','127.0.0.1'),(56,'2026-10-04 14:52:06',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED EXIT for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already outside on trip since 2026-10-04 14:50:49','127.0.0.1'),(57,'2026-10-04 14:52:07',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED EXIT for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already outside on trip since 2026-10-04 14:50:49','127.0.0.1'),(58,'2026-10-04 14:52:07',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED EXIT for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already outside on trip since 2026-10-04 14:50:49','127.0.0.1'),(59,'2026-10-04 14:57:16',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(60,'2026-10-04 14:57:27',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(61,'2026-10-04 15:04:19',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(62,'2026-10-04 15:04:20',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(63,'2026-10-04 15:08:11',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by tiger. Reason: Operator manual outbound dispatch','127.0.0.1'),(64,'2026-10-04 15:08:51',1,'tiger','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(65,'2026-10-04 15:09:04',1,'tiger','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(66,'2026-10-04 15:13:54',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.104'),(67,'2026-10-04 15:14:12',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-04 15:08:50','192.168.137.104'),(68,'2026-10-04 15:23:49',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-04 15:08:50','127.0.0.1'),(69,'2026-10-04 15:25:26',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(70,'2026-10-04 15:25:26',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(71,'2026-10-04 15:28:04',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(72,'2026-10-04 15:28:05',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(73,'2026-10-04 15:29:55',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.104'),(74,'2026-10-05 04:08:17',NULL,'SYSTEM','LOGIN_FAILED',NULL,NULL,'Failed login attempt with username \'mtnco\'','127.0.0.1'),(75,'2026-10-05 04:08:22',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(76,'2026-10-05 04:32:41',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.131'),(77,'2026-10-05 04:33:25',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.131'),(78,'2026-10-05 04:35:31',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.131'),(79,'2026-10-05 04:35:36',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.131'),(80,'2026-10-05 04:39:05',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 3m 28s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(81,'2026-10-05 05:43:48',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(82,'2026-10-05 05:44:02',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 13s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(83,'2026-10-05 05:47:21',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(84,'2026-10-05 05:51:28',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(85,'2026-10-05 05:51:43',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(86,'2026-10-05 05:53:09',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized RETURN (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(87,'2026-10-05 05:53:50',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(88,'2026-10-05 05:54:52',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 1m 1s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(89,'2026-10-05 05:57:18',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.113'),(90,'2026-10-05 05:57:32',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(91,'2026-10-05 05:59:06',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(92,'2026-10-05 06:00:13',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(93,'2026-10-05 06:01:33',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.113'),(94,'2026-10-05 06:47:52',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by tiger. Reason: Operator manual outbound dispatch','127.0.0.1'),(95,'2026-10-05 06:48:45',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 53s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(96,'2026-10-05 08:06:11',NULL,'SYSTEM','LOGIN_FAILED',NULL,NULL,'Failed login attempt with username \'TIGER\'','127.0.0.1'),(97,'2026-10-05 08:06:18',NULL,'SYSTEM','LOGIN_FAILED',NULL,NULL,'Failed login attempt with username \'tiger\'','127.0.0.1'),(98,'2026-10-05 08:06:37',NULL,'SYSTEM','LOGIN_FAILED',NULL,NULL,'Failed login attempt with username \'tiger\'','127.0.0.1'),(99,'2026-10-05 08:06:49',NULL,'SYSTEM','LOGIN_FAILED',NULL,NULL,'Failed login attempt with username \'co\'','127.0.0.1'),(100,'2026-10-05 08:07:41',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(101,'2026-10-06 03:10:16',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(102,'2026-10-06 03:12:15',NULL,'SYSTEM','LOGIN_FAILED',NULL,NULL,'Failed login attempt with username \'tiger\'','192.168.137.1'),(103,'2026-10-06 03:14:36',1,'tiger','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','127.0.0.1'),(104,'2026-10-06 03:14:44',1,'tiger','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','127.0.0.1'),(105,'2026-10-06 03:15:03',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by tiger. Reason: Operator manual outbound dispatch','127.0.0.1'),(106,'2026-10-06 03:16:05',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 1m 1s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(107,'2026-10-06 03:16:19',1,'tiger','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','127.0.0.1'),(108,'2026-10-06 03:16:27',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by tiger. Reason: Operator manual outbound dispatch','127.0.0.1'),(109,'2026-10-06 03:24:53',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 8m 25s. Reason: 5454','127.0.0.1'),(110,'2026-10-06 03:25:24',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by tiger. Reason: 222','127.0.0.1'),(111,'2026-10-06 04:13:45',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.210'),(112,'2026-10-06 04:14:29',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.210'),(113,'2026-10-06 04:17:10',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.210'),(114,'2026-10-06 04:21:19',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.210'),(115,'2026-10-06 04:21:32',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.210'),(116,'2026-10-06 04:28:13',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 6m 40s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(117,'2026-10-06 04:30:52',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.210'),(118,'2026-10-06 04:31:14',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 21s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(119,'2026-10-06 04:43:59',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Car) via Main Gate RFID Reader (ESP32)','192.168.137.210'),(120,'2026-10-06 04:45:12',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 1m 13s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(121,'2026-10-06 05:12:10',1,'tiger','DATABASE_BACKUP',NULL,NULL,'Created database backup: \'backup_gate_20261006_051209.db\'','127.0.0.1'),(122,'2026-10-06 05:23:22',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(123,'2026-10-06 05:30:06',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by tiger. Reason: test','127.0.0.1'),(124,'2026-10-06 06:14:06',NULL,'SYSTEM','VEHICLE_CREATE','TEST9999',NULL,'Created vehicle \'TEST9999\' (Jeep, Status: AUTHORIZED)','127.0.0.1'),(125,'2026-10-06 06:18:28',NULL,'SYSTEM','VEHICLE_CREATE','BA8888Z',NULL,'Created vehicle \'BA8888Z\' (Truck, Status: AUTHORIZED)','127.0.0.1'),(126,'2026-10-06 06:18:28',NULL,'SYSTEM','VEHICLE_UPDATE','BA8888Z',NULL,'Updated vehicle \'BA8888Z\' details (Status: AUTHORIZED)','127.0.0.1'),(127,'2026-10-06 06:23:33',NULL,'SYSTEM','VEHICLE_CREATE','BA9999X',NULL,'Created vehicle \'BA9999X\' (Tata YODHA, Status: AUTHORIZED)','127.0.0.1'),(128,'2026-10-06 06:48:47',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 1h 18m 40s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(129,'2026-10-06 06:55:38',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.221'),(130,'2026-10-06 06:56:02',1,'tiger','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by tiger. Trip Duration: 23s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(131,'2026-10-06 06:56:08',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'E9C9ED05\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','192.168.137.221'),(132,'2026-10-06 06:56:47',NULL,'SYSTEM','DRIVER_CREATE',NULL,NULL,'Created Driver profile: \'Subedar Balram Singh\' (JC-543210M, Hill Driving: YES, Status: AUTHORIZED)','127.0.0.1'),(133,'2026-10-06 06:56:47',NULL,'SYSTEM','DRIVER_CREATE',NULL,NULL,'Created Driver profile: \'Sepoy Kuldeep Yadav\' (JC-654321P, Hill Driving: NO, Status: NOT AUTHORIZED)','127.0.0.1'),(134,'2026-10-06 07:04:41',1,'tiger','DRIVER_CREATE',NULL,NULL,'Created Driver profile: \'Yawar WANI\' (40307508, Hill Driving: YES, Status: AUTHORIZED)','127.0.0.1'),(135,'2026-10-06 07:05:14',1,'tiger','DRIVER_CREATE',NULL,NULL,'Created Driver profile: \'Yawar WANI\' (44545656, Hill Driving: YES, Status: AUTHORIZED)','127.0.0.1'),(136,'2026-10-06 07:05:37',1,'tiger','DRIVER_CREATE',NULL,NULL,'Created Driver profile: \'KARTHICK\' (2456644, Hill Driving: NO, Status: NOT AUTHORIZED)','127.0.0.1'),(137,'2026-10-06 07:12:57',1,'tiger','DRIVER_CREATE',NULL,NULL,'Created Driver profile: \'ayyaz\' (46465, Hill Driving: YES, Status: AUTHORIZED)','127.0.0.1'),(138,'2026-10-06 07:32:46',1,'tiger','LOGOUT',NULL,NULL,'User \'tiger\' logged out','127.0.0.1'),(139,'2026-10-06 07:32:55',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(140,'2026-10-06 07:41:33',1,'tiger','LOGOUT',NULL,NULL,'User \'tiger\' logged out','127.0.0.1'),(141,'2026-10-06 07:42:24',2,'maingate','LOGIN',NULL,NULL,'User \'maingate\' logged in successfully (MAINGATE)','127.0.0.1'),(142,'2026-10-06 07:50:22',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.67'),(143,'2026-10-06 07:50:50',2,'maingate','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by maingate. Reason: Operator manual outbound dispatch','127.0.0.1'),(144,'2026-10-06 07:53:03',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.167'),(145,'2026-10-06 07:54:22',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.62'),(146,'2026-10-06 09:02:33',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(147,'2026-10-06 09:03:47',1,'tiger','LOGOUT',NULL,NULL,'User \'tiger\' logged out','127.0.0.1'),(148,'2026-10-06 09:04:00',2,'maingate','LOGIN',NULL,NULL,'User \'maingate\' logged in successfully (MAINGATE)','127.0.0.1'),(149,'2026-10-06 09:05:06',2,'maingate','LOGOUT',NULL,NULL,'User \'maingate\' logged out','127.0.0.1'),(150,'2026-10-06 09:05:08',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(151,'2026-10-06 09:05:59',1,'tiger','LOGOUT',NULL,NULL,'User \'tiger\' logged out','127.0.0.1'),(152,'2026-10-06 09:06:06',2,'maingate','LOGIN',NULL,NULL,'User \'maingate\' logged in successfully (MAINGATE)','127.0.0.1'),(153,'2026-10-06 09:12:45',2,'maingate','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by maingate. Reason: Operator manual outbound dispatch','127.0.0.1'),(154,'2026-10-06 09:13:39',2,'maingate','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','127.0.0.1'),(155,'2026-10-06 09:16:48',2,'maingate','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL DISPATCH (EXIT) recorded for \'24BH9074C\' by maingate. Reason: Operator manual outbound dispatch','127.0.0.1'),(156,'2026-10-06 09:18:34',2,'maingate','MANUAL_OVERRIDE','24BH9074C',NULL,'MANUAL RETURN (IN Depot) recorded for \'24BH9074C\' by maingate. Trip Duration: 1m 46s. Reason: Vehicle returned to depot (Arrival Check-In)','127.0.0.1'),(157,'2026-10-06 09:22:08',2,'maingate','LOGOUT',NULL,NULL,'User \'maingate\' logged out','127.0.0.1'),(158,'2026-10-06 09:22:10',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(159,'2026-10-06 09:28:11',1,'tiger','LOGOUT',NULL,NULL,'User \'tiger\' logged out','127.0.0.1'),(160,'2026-10-06 09:28:13',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(161,'2026-10-06 09:28:15',1,'tiger','LOGOUT',NULL,NULL,'User \'tiger\' logged out','127.0.0.1'),(162,'2026-10-06 09:28:22',2,'maingate','LOGIN',NULL,NULL,'User \'maingate\' logged in successfully (MAINGATE)','127.0.0.1'),(163,'2026-10-06 09:32:33',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.25'),(164,'2026-10-06 09:54:36',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(165,'2026-10-06 09:54:40',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(166,'2026-10-06 09:58:59',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(167,'2026-10-06 09:59:03',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(168,'2026-10-06 09:59:29',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.107'),(169,'2026-10-06 09:59:36',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.107'),(170,'2026-10-06 09:59:45',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.107'),(171,'2026-10-06 09:59:55',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.107'),(172,'2026-10-06 10:00:07',NULL,'SYSTEM','VEHICLE_EXIT','24BH9074C','GATE01','Authorized EXIT (Outbound Dispatch) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.107'),(173,'2026-10-06 10:00:11',NULL,'SYSTEM','VEHICLE_ENTRY','24BH9074C','GATE01','Authorized ENTRY (Arrival to Depot) for 24BH9074C (Scorpio) via Main Gate RFID Reader (ESP32)','192.168.137.107'),(174,'2026-10-06 10:00:18',2,'maingate','LOGOUT',NULL,NULL,'User \'maingate\' logged out','127.0.0.1'),(175,'2026-10-06 10:00:21',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(176,'2026-10-06 10:00:29',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'E9C9ED05\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','192.168.137.107'),(177,'2026-10-06 10:00:35',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'E9C9ED05\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','192.168.137.107'),(178,'2026-10-06 10:00:40',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'E9C9ED05\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','192.168.137.107'),(179,'2026-10-06 10:00:45',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'E9C9ED05\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','192.168.137.107'),(180,'2026-10-06 10:01:00',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(181,'2026-10-06 10:01:03',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(182,'2026-10-06 10:01:10',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(183,'2026-10-06 10:01:20',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(184,'2026-10-06 10:01:26',NULL,'SYSTEM','DENIED_ATTEMPT','24BH9074C','1','DENIED ENTRY for UID \'52932A5C\' / Plate \'24BH9074C\'. Reason: DUPLICATE_ENTRY. Vehicle already entered at 2026-10-05 04:32:41','192.168.137.107'),(185,'2026-10-06 10:03:47',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'E9C9ED05\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','192.168.137.107'),(186,'2026-10-06 10:04:09',NULL,'SYSTEM','DENIED_ATTEMPT',NULL,'1','DENIED ENTRY for UID \'E9C9ED05\' / Plate \'Unknown\'. Reason: UNKNOWN_RFID. Unregistered RFID tag scanned','192.168.137.107');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `camera_configs`
--

DROP TABLE IF EXISTS `camera_configs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `camera_configs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `camera_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `camera_name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rtsp_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `resolution` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `last_seen` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_camera_configs_camera_id` (`camera_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `camera_configs`
--

LOCK TABLES `camera_configs` WRITE;
/*!40000 ALTER TABLE `camera_configs` DISABLE KEYS */;
/*!40000 ALTER TABLE `camera_configs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `denied_attempts`
--

DROP TABLE IF EXISTS `denied_attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `denied_attempts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `rfid_uid` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vehicle_number` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vehicle_id` int DEFAULT NULL,
  `device_id` int DEFAULT NULL,
  `direction` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reason` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `operator_id` int DEFAULT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `is_demo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `vehicle_id` (`vehicle_id`),
  KEY `device_id` (`device_id`),
  KEY `operator_id` (`operator_id`),
  KEY `ix_denied_attempts_rfid_uid` (`rfid_uid`),
  KEY `ix_denied_attempts_reason` (`reason`),
  KEY `ix_denied_attempts_event_id` (`event_id`),
  KEY `ix_denied_attempts_vehicle_number` (`vehicle_number`),
  KEY `ix_denied_attempts_timestamp` (`timestamp`),
  CONSTRAINT `denied_attempts_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`),
  CONSTRAINT `denied_attempts_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `denied_attempts_ibfk_3` FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `denied_attempts`
--

LOCK TABLES `denied_attempts` WRITE;
/*!40000 ALTER TABLE `denied_attempts` DISABLE KEYS */;
INSERT INTO `denied_attempts` VALUES (1,'2026-10-05 05:57:18','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-872183-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(2,'2026-10-06 03:14:36','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','b0d8c4fb-1897-4765-9925-c5d0b7ec66f2',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(3,'2026-10-06 03:14:44','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','26cb4137-094a-4f4a-a3e4-c287f3a7be95',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(4,'2026-10-06 03:16:19','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','2ac6a517-4b01-49ed-8974-95f250ec2530',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(5,'2026-10-06 04:14:29','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-47592-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(6,'2026-10-06 04:17:10','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-208527-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(7,'2026-10-06 04:21:19','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-457561-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(8,'2026-10-06 06:56:08','E9C9ED05',NULL,NULL,1,'ENTRY','UNKNOWN_RFID','GATE01-50432-E9C9ED05',NULL,'Unregistered RFID tag scanned',0),(9,'2026-10-06 07:50:22','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-34109-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(10,'2026-10-06 07:54:22','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-274529-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(11,'2026-10-06 09:32:33','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-45009-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(12,'2026-10-06 09:54:36','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-46932-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(13,'2026-10-06 09:54:40','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-51039-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(14,'2026-10-06 09:58:59','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-14464-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(15,'2026-10-06 09:59:03','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-18823-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(16,'2026-10-06 10:00:29','E9C9ED05',NULL,NULL,1,'ENTRY','UNKNOWN_RFID','GATE01-104371-E9C9ED05',NULL,'Unregistered RFID tag scanned',0),(17,'2026-10-06 10:00:35','E9C9ED05',NULL,NULL,1,'ENTRY','UNKNOWN_RFID','GATE01-110818-E9C9ED05',NULL,'Unregistered RFID tag scanned',0),(18,'2026-10-06 10:00:40','E9C9ED05',NULL,NULL,1,'ENTRY','UNKNOWN_RFID','GATE01-116019-E9C9ED05',NULL,'Unregistered RFID tag scanned',0),(19,'2026-10-06 10:00:45','E9C9ED05',NULL,NULL,1,'ENTRY','UNKNOWN_RFID','GATE01-120757-E9C9ED05',NULL,'Unregistered RFID tag scanned',0),(20,'2026-10-06 10:01:00','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-136087-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(21,'2026-10-06 10:01:03','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-139263-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(22,'2026-10-06 10:01:10','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-146209-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(23,'2026-10-06 10:01:20','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-156262-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(24,'2026-10-06 10:01:26','52932A5C','24BH9074C',1,1,'ENTRY','DUPLICATE_ENTRY','GATE01-162017-52932A5C',NULL,'Vehicle already entered at 2026-10-05 04:32:41',0),(25,'2026-10-06 10:03:47','E9C9ED05',NULL,NULL,1,'ENTRY','UNKNOWN_RFID','GATE01-302698-E9C9ED05',NULL,'Unregistered RFID tag scanned',0),(26,'2026-10-06 10:04:09','E9C9ED05',NULL,NULL,1,'ENTRY','UNKNOWN_RFID','GATE01-325458-E9C9ED05',NULL,'Unregistered RFID tag scanned',0);
/*!40000 ALTER TABLE `denied_attempts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `device_events`
--

DROP TABLE IF EXISTS `device_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `device_events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `device_id` int NOT NULL,
  `event_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_payload` text COLLATE utf8mb4_unicode_ci,
  `response_summary` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_device_events_event_id` (`event_id`),
  KEY `ix_device_events_device_id` (`device_id`),
  KEY `ix_device_events_timestamp` (`timestamp`),
  CONSTRAINT `device_events_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `device_events`
--

LOCK TABLES `device_events` WRITE;
/*!40000 ALTER TABLE `device_events` DISABLE KEYS */;
INSERT INTO `device_events` VALUES (1,1,'SCAN','93a4410b-2337-4b9b-aa66-aa141656b2e2','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Checked into depot.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"40s\", \"movement_id\": 1, \"event_id\": \"93a4410b-2337-4b9b-aa66-aa141656b2e2\", \"timestamp\": \"2026-10-04T15:08:50.878576\"}','ENTRY_ALLOWED - Vehicle return authorized. Checked into depot.','2026-10-04 15:08:51'),(2,1,'SCAN','6ff99030-24c8-49c9-be55-4beb38db2ae5','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 2, \"event_id\": \"6ff99030-24c8-49c9-be55-4beb38db2ae5\", \"timestamp\": \"2026-10-04T15:09:03.853956\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-04 15:09:04'),(3,1,'SCAN','GATE01-3440-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"4m 50s\", \"movement_id\": 2, \"event_id\": \"GATE01-3440-52932A5C\", \"timestamp\": \"2026-10-04T15:13:54.464568\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-04 15:13:54'),(4,1,'SCAN',NULL,'{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 1, \"event_id\": \"\", \"timestamp\": \"2026-10-04T15:25:26.129363\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-04 15:25:26'),(5,1,'SCAN',NULL,'{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Checked into depot.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"0s\", \"movement_id\": 1, \"event_id\": \"\", \"timestamp\": \"2026-10-04T15:25:26.359357\"}','ENTRY_ALLOWED - Vehicle return authorized. Checked into depot.','2026-10-04 15:25:26'),(6,1,'SCAN','9d96926e-2a14-4e35-a048-60013e238246','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 1, \"event_id\": \"9d96926e-2a14-4e35-a048-60013e238246\", \"timestamp\": \"2026-10-04T15:28:04.450133\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-04 15:28:04'),(7,1,'SCAN','1364c456-aec5-4427-88fe-49042d5812bc','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Checked into depot.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"0s\", \"movement_id\": 1, \"event_id\": \"1364c456-aec5-4427-88fe-49042d5812bc\", \"timestamp\": \"2026-10-04T15:28:04.712328\"}','ENTRY_ALLOWED - Vehicle return authorized. Checked into depot.','2026-10-04 15:28:05'),(8,1,'SCAN','GATE01-963846-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 1, \"event_id\": \"GATE01-963846-52932A5C\", \"timestamp\": \"2026-10-04T15:29:54.830899\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-04 15:29:55'),(9,1,'SCAN','GATE01-12757-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Checked into depot.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"Amit Deshmukh\", \"movement_status\": \"INSIDE\", \"duration\": \"13h 2m 46s\", \"movement_id\": 1, \"event_id\": \"GATE01-12757-52932A5C\", \"timestamp\": \"2026-10-05T04:32:41.173313\"}','ENTRY_ALLOWED - Vehicle return authorized. Checked into depot.','2026-10-05 04:32:41'),(10,1,'SCAN','GATE01-57443-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 2, \"event_id\": \"GATE01-57443-52932A5C\", \"timestamp\": \"2026-10-05T04:33:25.458477\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 04:33:25'),(11,1,'SCAN','GATE01-183162-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Checked into depot.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"Amit Deshmukh\", \"movement_status\": \"INSIDE\", \"duration\": \"2m 5s\", \"movement_id\": 2, \"event_id\": \"GATE01-183162-52932A5C\", \"timestamp\": \"2026-10-05T04:35:31.169052\"}','ENTRY_ALLOWED - Vehicle return authorized. Checked into depot.','2026-10-05 04:35:31'),(12,1,'SCAN','GATE01-188066-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 3, \"event_id\": \"GATE01-188066-52932A5C\", \"timestamp\": \"2026-10-05T04:35:36.142107\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 04:35:36'),(13,1,'SCAN','GATE01-62354-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 4, \"event_id\": \"GATE01-62354-52932A5C\", \"timestamp\": \"2026-10-05T05:43:48.501322\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 05:43:49'),(14,1,'SCAN','GATE01-274711-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 5, \"event_id\": \"GATE01-274711-52932A5C\", \"timestamp\": \"2026-10-05T05:47:20.852538\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 05:47:21'),(15,1,'SCAN','GATE01-518286-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Checked into depot.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"4m 6s\", \"movement_id\": 5, \"event_id\": \"GATE01-518286-52932A5C\", \"timestamp\": \"2026-10-05T05:51:27.742259\"}','ENTRY_ALLOWED - Vehicle return authorized. Checked into depot.','2026-10-05 05:51:28'),(16,1,'SCAN','GATE01-536844-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 6, \"event_id\": \"GATE01-536844-52932A5C\", \"timestamp\": \"2026-10-05T05:51:43.118958\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 05:51:43'),(17,1,'SCAN','GATE01-622837-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Checked into depot.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"Arsh Mulla\", \"movement_status\": \"INSIDE\", \"duration\": \"1m 26s\", \"movement_id\": 6, \"event_id\": \"GATE01-622837-52932A5C\", \"timestamp\": \"2026-10-05T05:53:09.137406\"}','ENTRY_ALLOWED - Vehicle return authorized. Checked into depot.','2026-10-05 05:53:09'),(18,1,'SCAN','GATE01-663704-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 7, \"event_id\": \"GATE01-663704-52932A5C\", \"timestamp\": \"2026-10-05T05:53:49.852045\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 05:53:50'),(19,1,'SCAN','GATE01-885460-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 8, \"event_id\": \"GATE01-885460-52932A5C\", \"timestamp\": \"2026-10-05T05:57:31.820211\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 05:57:32'),(20,1,'SCAN','GATE01-979671-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"1m 34s\", \"movement_id\": 8, \"event_id\": \"GATE01-979671-52932A5C\", \"timestamp\": \"2026-10-05T05:59:06.075458\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-05 05:59:06'),(21,1,'SCAN','GATE01-1047163-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 9, \"event_id\": \"GATE01-1047163-52932A5C\", \"timestamp\": \"2026-10-05T06:00:13.284135\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-05 06:00:13'),(22,1,'SCAN','GATE01-1126715-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"1m 19s\", \"movement_id\": 9, \"event_id\": \"GATE01-1126715-52932A5C\", \"timestamp\": \"2026-10-05T06:01:32.817604\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-05 06:01:33'),(23,1,'SCAN','GATE01-2953-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"48m 20s\", \"movement_id\": 13, \"event_id\": \"GATE01-2953-52932A5C\", \"timestamp\": \"2026-10-06T04:13:44.708536\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-06 04:13:45'),(24,1,'SCAN','GATE01-470277-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 14, \"event_id\": \"GATE01-470277-52932A5C\", \"timestamp\": \"2026-10-06T04:21:32.004534\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-06 04:21:32'),(25,1,'SCAN','GATE01-3275-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 15, \"event_id\": \"GATE01-3275-52932A5C\", \"timestamp\": \"2026-10-06T04:30:52.058623\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-06 04:30:52'),(26,1,'SCAN','GATE01-4297-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Car\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 16, \"event_id\": \"GATE01-4297-52932A5C\", \"timestamp\": \"2026-10-06T04:43:58.753428\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-06 04:43:59'),(27,1,'SCAN','GATE01-20548-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 18, \"event_id\": \"GATE01-20548-52932A5C\", \"timestamp\": \"2026-10-06T06:55:37.902963\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-06 06:55:38'),(28,1,'SCAN','GATE01-194758-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"2m 12s\", \"movement_id\": 19, \"event_id\": \"GATE01-194758-52932A5C\", \"timestamp\": \"2026-10-06T07:53:02.649792\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-06 07:53:03'),(29,1,'SCAN','2fbc1a27-8fac-4022-b9e7-adefb7b3e623','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"54s\", \"movement_id\": 20, \"event_id\": \"2fbc1a27-8fac-4022-b9e7-adefb7b3e623\", \"timestamp\": \"2026-10-06T09:13:39.048399\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-06 09:13:39'),(30,1,'SCAN','GATE01-44577-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 22, \"event_id\": \"GATE01-44577-52932A5C\", \"timestamp\": \"2026-10-06T09:59:28.706059\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-06 09:59:29'),(31,1,'SCAN','GATE01-52019-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"7s\", \"movement_id\": 22, \"event_id\": \"GATE01-52019-52932A5C\", \"timestamp\": \"2026-10-06T09:59:36.132055\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-06 09:59:36'),(32,1,'SCAN','GATE01-60736-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 23, \"event_id\": \"GATE01-60736-52932A5C\", \"timestamp\": \"2026-10-06T09:59:45.068552\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-06 09:59:45'),(33,1,'SCAN','GATE01-71229-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"10s\", \"movement_id\": 23, \"event_id\": \"GATE01-71229-52932A5C\", \"timestamp\": \"2026-10-06T09:59:55.288273\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-06 09:59:55'),(34,1,'SCAN','GATE01-82975-52932A5C','{\"success\": true, \"decision\": \"EXIT_RECORDED\", \"message\": \"Vehicle exit authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"OUTSIDE\", \"duration\": \"N/A\", \"movement_id\": 24, \"event_id\": \"GATE01-82975-52932A5C\", \"timestamp\": \"2026-10-06T10:00:07.064706\"}','EXIT_RECORDED - Vehicle exit authorized. Gate permitted.','2026-10-06 10:00:07'),(35,1,'SCAN','GATE01-87014-52932A5C','{\"success\": true, \"decision\": \"ENTRY_ALLOWED\", \"message\": \"Vehicle return authorized. Gate permitted.\", \"vehicle_number\": \"24BH9074C\", \"vehicle_type\": \"Scorpio\", \"driver_name\": \"AYYAJ MULLA\", \"movement_status\": \"INSIDE\", \"duration\": \"4s\", \"movement_id\": 24, \"event_id\": \"GATE01-87014-52932A5C\", \"timestamp\": \"2026-10-06T10:00:11.178505\"}','ENTRY_ALLOWED - Vehicle return authorized. Gate permitted.','2026-10-06 10:00:11');
/*!40000 ALTER TABLE `device_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devices`
--

DROP TABLE IF EXISTS `devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `device_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `device_name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `device_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gate` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direction` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_seen` datetime DEFAULT NULL,
  `last_event` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `firmware_version` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `api_key_hash` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_devices_device_id` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devices`
--

LOCK TABLES `devices` WRITE;
/*!40000 ALTER TABLE `devices` DISABLE KEYS */;
INSERT INTO `devices` VALUES (1,'GATE01','Main Gate RFID Reader (ESP32)','ESP32 RFID','Main Gate','EXIT','192.168.137.107','ONLINE','2026-10-06 10:04:37','ENTRY (RETURN): 24BH9074C','v1.0.0','scrypt:32768:8:1$ldMVOMqVjLVfUWxI$33de89e744311fad3428f311dc6ebbbafc4e1e1af71f8ae6eb7562928583107b8cd680c1efd3bf0b136917ff8066e83f1c5a3ea197ee45f515f4d6265c132462',1,'2026-10-03 13:09:34');
/*!40000 ALTER TABLE `devices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `drivers`
--

DROP TABLE IF EXISTS `drivers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `drivers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `armynumber` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `driver_rank` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `section` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hill_driving` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'NO',
  `auth_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'NOT AUTHORIZED',
  `authorized_vehicle_types` text COLLATE utf8mb4_unicode_ci,
  `license_number` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mobile_number` varchar(24) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `designation` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_drivers_is_active` (`is_active`),
  KEY `ix_drivers_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `drivers`
--

LOCK TABLES `drivers` WRITE;
/*!40000 ALTER TABLE `drivers` DISABLE KEYS */;
INSERT INTO `drivers` VALUES (1,'Yawar WANI','44545656','TYURU','1 coy','PP','YES','AUTHORIZED','Gypsy, 2.5 Ton, ALS, LRV, HMV, Tata YODHA, ALS W/B, R/E, Fortuner, Scorpio','3444664646464','7879464641','TYURU',1,NULL,'2026-10-06 07:05:14','2026-10-06 07:05:14'),(2,'KARTHICK','2456644','OUEOT','1 COY','PP','NO','NOT AUTHORIZED',NULL,'4444464446467','4464','OUEOT',1,NULL,'2026-10-06 07:05:37','2026-10-06 07:05:37'),(3,'ayyaz','46465','OC','1 COY','MT','YES','AUTHORIZED','Gypsy, 2.5 Ton, ALS, LRV, HMV, Tata YODHA, ALS W/B, R/E, Fortuner, Scorpio','545464446','55777777978','OC',1,NULL,'2026-10-06 07:12:57','2026-10-06 07:12:57');
/*!40000 ALTER TABLE `drivers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rfid_cards`
--

DROP TABLE IF EXISTS `rfid_cards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rfid_cards` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uid` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `vehicle_id` int DEFAULT NULL,
  `card_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `assigned_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `is_demo` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_rfid_cards_uid` (`uid`),
  KEY `ix_rfid_cards_card_status` (`card_status`),
  KEY `ix_rfid_cards_vehicle_id` (`vehicle_id`),
  CONSTRAINT `rfid_cards_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rfid_cards`
--

LOCK TABLES `rfid_cards` WRITE;
/*!40000 ALTER TABLE `rfid_cards` DISABLE KEYS */;
INSERT INTO `rfid_cards` VALUES (1,'52932A5C',1,'ACTIVE','2026-10-04','2026-10-31','NB SUB AYYAJ MULLA',0,'2026-10-03 14:09:06','2026-10-04 14:46:23');
/*!40000 ALTER TABLE `rfid_cards` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_settings`
--

DROP TABLE IF EXISTS `system_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_system_settings_key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_settings`
--

LOCK TABLES `system_settings` WRITE;
/*!40000 ALTER TABLE `system_settings` DISABLE KEYS */;
INSERT INTO `system_settings` VALUES (1,'system_name','Smart RFID + ANPR Vehicle Gate System','Display name of the application','2026-10-03 12:51:21'),(2,'gate_direction_mode','ENTRY_ONLY','Default direction mode (ENTRY_ONLY, EXIT_ONLY, MANUAL_DIRECTION, FUTURE_SEPARATE_ENTRY_EXIT_READERS)','2026-10-06 10:00:10'),(3,'scan_cooldown_seconds','3','Cooldown duration between scans for same RFID in seconds','2026-10-03 12:51:21'),(4,'device_heartbeat_timeout','35','Seconds before an inactive device is marked OFFLINE','2026-10-03 12:51:21'),(5,'barrier_auto_close_delay','4','Seconds to simulate barrier gate open before auto-closing','2026-10-03 12:51:21'),(6,'anpr_confidence_threshold','80.0','Minimum confidence score (%) for ANPR auto-match','2026-10-03 12:51:21'),(7,'dashboard_refresh_interval','5','Dashboard auto-refresh interval in seconds','2026-10-03 12:51:21'),(8,'demo_mode_enabled','0','Whether simulated demo controls and quick actions are shown','2026-10-03 12:51:21');
/*!40000 ALTER TABLE `system_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'tiger','scrypt:32768:8:1$qkBNFsSD1GP67ewH$43196699ec01deb0861e4d4ac85c4d03c69bb31c3c88ea1ed3c85555390f4cfc3ed6dd7777364642cc22d1b9d8dae3457359eafd4dff73b71b95367f4ae3db5d','tiger',NULL,'ADMIN',1,'2026-10-03 13:04:21','2026-10-06 10:00:21'),(2,'maingate','scrypt:32768:8:1$Axj7QbCuxicqbAqw$027345059e571e0d5fc60905952ed094e78d2618adc6eaccd851b16e5d8e9b93a26e93ceea316b2f9825c2318d80a1f8d2fbbfd37b3863cf8c98c98ff3900ec4','Main Gate Operator','maingate@depot.local','MAINGATE',1,'2026-10-06 07:40:13','2026-10-06 09:28:22');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicle_movements`
--

DROP TABLE IF EXISTS `vehicle_movements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicle_movements` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vehicle_id` int NOT NULL,
  `rfid_card_id` int DEFAULT NULL,
  `driver_id` int DEFAULT NULL,
  `driver_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entry_time` datetime NOT NULL,
  `entry_device_id` int DEFAULT NULL,
  `entry_operator_id` int DEFAULT NULL,
  `exit_time` datetime DEFAULT NULL,
  `exit_device_id` int DEFAULT NULL,
  `exit_operator_id` int DEFAULT NULL,
  `duration_seconds` int DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direction` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_manual` tinyint(1) NOT NULL,
  `manual_reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `is_demo` tinyint(1) NOT NULL,
  `entry_event_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `exit_event_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `entry_device_id` (`entry_device_id`),
  KEY `entry_operator_id` (`entry_operator_id`),
  KEY `exit_device_id` (`exit_device_id`),
  KEY `exit_operator_id` (`exit_operator_id`),
  KEY `ix_vehicle_movements_entry_time` (`entry_time`),
  KEY `ix_vehicle_movements_exit_event_id` (`exit_event_id`),
  KEY `ix_vehicle_movements_vehicle_id` (`vehicle_id`),
  KEY `ix_vehicle_movements_driver_id` (`driver_id`),
  KEY `ix_vehicle_movements_entry_event_id` (`entry_event_id`),
  KEY `ix_vehicle_movements_rfid_card_id` (`rfid_card_id`),
  KEY `ix_vehicle_movements_exit_time` (`exit_time`),
  KEY `ix_vehicle_movements_status` (`status`),
  CONSTRAINT `vehicle_movements_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_2` FOREIGN KEY (`rfid_card_id`) REFERENCES `rfid_cards` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_4` FOREIGN KEY (`entry_device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_5` FOREIGN KEY (`entry_operator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_6` FOREIGN KEY (`exit_device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_7` FOREIGN KEY (`exit_operator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicle_movements`
--

LOCK TABLES `vehicle_movements` WRITE;
/*!40000 ALTER TABLE `vehicle_movements` DISABLE KEYS */;
INSERT INTO `vehicle_movements` VALUES (1,1,1,NULL,'AYYAJ MULLA','2026-10-05 04:32:41',1,NULL,'2026-10-04 15:29:55',1,NULL,46966,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-12757-52932A5C','GATE01-963846-52932A5C','2026-10-04 15:29:55'),(2,1,1,6,'Amit Deshmukh','2026-10-05 04:35:31',1,NULL,'2026-10-05 04:33:25',1,NULL,125,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-183162-52932A5C','GATE01-57443-52932A5C','2026-10-05 04:33:25'),(3,1,1,NULL,'AYYAJ MULLA','2026-10-05 04:39:05',NULL,1,'2026-10-05 04:35:36',1,NULL,208,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','Vehicle Returned to Depot (Arrival Check-In)',0,NULL,'GATE01-188066-52932A5C','2026-10-05 04:35:36'),(4,1,1,NULL,'AYYAJ MULLA','2026-10-05 05:44:02',NULL,1,'2026-10-05 05:43:48',1,NULL,13,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','Vehicle Returned to Depot (Arrival Check-In)',0,NULL,'GATE01-62354-52932A5C','2026-10-05 05:43:48'),(5,1,1,NULL,'AYYAJ MULLA','2026-10-05 05:51:28',1,NULL,'2026-10-05 05:47:21',1,NULL,246,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-518286-52932A5C','GATE01-274711-52932A5C','2026-10-05 05:47:21'),(6,1,1,NULL,'AYYAJ MULLA','2026-10-05 05:53:09',1,NULL,'2026-10-05 05:51:43',1,NULL,86,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-622837-52932A5C','GATE01-536844-52932A5C','2026-10-05 05:51:43'),(7,1,1,NULL,'AYYAJ MULLA','2026-10-05 05:54:52',NULL,1,'2026-10-05 05:53:50',1,NULL,61,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','Vehicle Returned to Depot (Arrival Check-In)',0,NULL,'GATE01-663704-52932A5C','2026-10-05 05:53:50'),(8,1,1,NULL,'AYYAJ MULLA','2026-10-05 05:59:06',1,NULL,'2026-10-05 05:57:32',1,NULL,94,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-979671-52932A5C','GATE01-885460-52932A5C','2026-10-05 05:57:32'),(9,1,1,NULL,'AYYAJ MULLA','2026-10-05 06:01:33',1,NULL,'2026-10-05 06:00:13',1,NULL,79,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-1126715-52932A5C','GATE01-1047163-52932A5C','2026-10-05 06:00:13'),(10,1,NULL,NULL,'AYYAJ MULLA','2026-10-05 06:48:45',NULL,1,'2026-10-05 06:47:52',NULL,1,53,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','MANUAL DISPATCH (EXIT):\nVehicle Returned to Depot (Arrival Check-In)',0,NULL,NULL,'2026-10-05 06:47:52'),(11,1,NULL,NULL,'AYYAJ MULLA','2026-10-06 03:16:05',NULL,1,'2026-10-06 03:15:03',NULL,1,61,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','MANUAL DISPATCH (EXIT):\nVehicle Returned to Depot (Arrival Check-In)',0,NULL,NULL,'2026-10-06 03:15:03'),(12,1,NULL,NULL,'AYYAJ MULLA','2026-10-06 03:24:53',NULL,1,'2026-10-06 03:16:27',NULL,1,505,'INSIDE','EXIT',1,'5454','MANUAL DISPATCH (EXIT):',0,NULL,NULL,'2026-10-06 03:16:27'),(13,1,NULL,NULL,'AYYAJ MULLA','2026-10-06 04:13:45',1,NULL,'2026-10-06 03:25:24',NULL,1,2900,'INSIDE','EXIT',1,'222','MANUAL DISPATCH (EXIT):',0,'GATE01-2953-52932A5C',NULL,'2026-10-06 03:25:24'),(14,1,1,NULL,'AYYAJ MULLA','2026-10-06 04:28:13',NULL,1,'2026-10-06 04:21:32',1,NULL,400,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','Vehicle Returned to Depot (Arrival Check-In)',0,NULL,'GATE01-470277-52932A5C','2026-10-06 04:21:32'),(15,1,1,NULL,'AYYAJ MULLA','2026-10-06 04:31:14',NULL,1,'2026-10-06 04:30:52',1,NULL,21,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','Vehicle Returned to Depot (Arrival Check-In)',0,NULL,'GATE01-3275-52932A5C','2026-10-06 04:30:52'),(16,1,1,NULL,'AYYAJ MULLA','2026-10-06 04:45:12',NULL,1,'2026-10-06 04:43:59',1,NULL,73,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','Vehicle Returned to Depot (Arrival Check-In)',0,NULL,'GATE01-4297-52932A5C','2026-10-06 04:43:59'),(17,1,NULL,NULL,'AYYAJ MULLA','2026-10-06 06:48:47',NULL,1,'2026-10-06 05:30:06',NULL,1,4720,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','MANUAL DISPATCH (EXIT):\nVehicle Returned to Depot (Arrival Check-In)',0,NULL,NULL,'2026-10-06 05:30:06'),(18,1,1,NULL,'AYYAJ MULLA','2026-10-06 06:56:02',NULL,1,'2026-10-06 06:55:38',1,NULL,23,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','Vehicle Returned to Depot (Arrival Check-In)',0,NULL,'GATE01-20548-52932A5C','2026-10-06 06:55:38'),(19,1,NULL,NULL,'AYYAJ MULLA','2026-10-06 07:53:03',1,NULL,'2026-10-06 07:50:50',NULL,2,132,'INSIDE','EXIT',1,'Operator manual outbound dispatch','MANUAL DISPATCH (EXIT):',0,'GATE01-194758-52932A5C',NULL,'2026-10-06 07:50:50'),(20,1,NULL,NULL,'AYYAJ MULLA','2026-10-06 09:13:39',1,NULL,'2026-10-06 09:12:45',NULL,2,54,'INSIDE','EXIT',1,'Operator manual outbound dispatch','MANUAL DISPATCH (EXIT):',0,'2fbc1a27-8fac-4022-b9e7-adefb7b3e623',NULL,'2026-10-06 09:12:45'),(21,1,NULL,NULL,'AYYAJ MULLA','2026-10-06 09:18:34',NULL,2,'2026-10-06 09:16:48',NULL,2,106,'INSIDE','EXIT',1,'Vehicle returned to depot (Arrival Check-In)','MANUAL DISPATCH (EXIT):\nVehicle Returned to Depot (Arrival Check-In)',0,NULL,NULL,'2026-10-06 09:16:48'),(22,1,1,NULL,'AYYAJ MULLA','2026-10-06 09:59:36',1,NULL,'2026-10-06 09:59:29',1,NULL,7,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-52019-52932A5C','GATE01-44577-52932A5C','2026-10-06 09:59:29'),(23,1,1,NULL,'AYYAJ MULLA','2026-10-06 09:59:55',1,NULL,'2026-10-06 09:59:45',1,NULL,10,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-71229-52932A5C','GATE01-60736-52932A5C','2026-10-06 09:59:45'),(24,1,1,NULL,'AYYAJ MULLA','2026-10-06 10:00:11',1,NULL,'2026-10-06 10:00:07',1,NULL,4,'INSIDE','EXIT',0,NULL,NULL,0,'GATE01-87014-52932A5C','GATE01-82975-52932A5C','2026-10-06 10:00:07');
/*!40000 ALTER TABLE `vehicle_movements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicles`
--

DROP TABLE IF EXISTS `vehicles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `registration_number` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `vehicle_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `issue_date` date DEFAULT NULL,
  `custodian_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `armynumber` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mobile_number` varchar(24) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `auth_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_demo` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_vehicles_registration_number` (`registration_number`),
  KEY `ix_vehicles_auth_status` (`auth_status`),
  KEY `ix_vehicles_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicles`
--

LOCK TABLES `vehicles` WRITE;
/*!40000 ALTER TABLE `vehicles` DISABLE KEYS */;
INSERT INTO `vehicles` VALUES (1,'24BH9074C','Scorpio',NULL,'AYYAJ MULLA','123','8130815049','AUTHORIZED',1,0,'2026-10-04 14:45:34','2026-10-04 14:45:34');
/*!40000 ALTER TABLE `vehicles` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-06 15:34:50
