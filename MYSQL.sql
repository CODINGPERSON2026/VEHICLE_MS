-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: vms
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
  `captured_plate` varchar(32) NOT NULL,
  `confidence` float NOT NULL,
  `matched_vehicle_id` int DEFAULT NULL,
  `rfid_event_id` varchar(64) DEFAULT NULL,
  `verification_status` varchar(32) DEFAULT NULL,
  `snapshot_path` varchar(255) DEFAULT NULL,
  `is_demo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `camera_id` (`camera_id`),
  KEY `matched_vehicle_id` (`matched_vehicle_id`),
  KEY `ix_anpr_events_rfid_event_id` (`rfid_event_id`),
  KEY `ix_anpr_events_captured_plate` (`captured_plate`),
  KEY `ix_anpr_events_timestamp` (`timestamp`),
  CONSTRAINT `anpr_events_ibfk_1` FOREIGN KEY (`camera_id`) REFERENCES `camera_configs` (`id`),
  CONSTRAINT `anpr_events_ibfk_2` FOREIGN KEY (`matched_vehicle_id`) REFERENCES `vehicles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anpr_events`
--

LOCK TABLES `anpr_events` WRITE;
/*!40000 ALTER TABLE `anpr_events` DISABLE KEYS */;
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
  `username` varchar(64) NOT NULL,
  `action` varchar(64) NOT NULL,
  `related_vehicle` varchar(64) DEFAULT NULL,
  `related_device` varchar(64) DEFAULT NULL,
  `description` text NOT NULL,
  `ip_address` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_audit_logs_user_id` (`user_id`),
  KEY `ix_audit_logs_action` (`action`),
  KEY `ix_audit_logs_timestamp` (`timestamp`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,'2026-10-07 17:30:58',1,'tiger','VEHICLE_CREATE','1234',NULL,'Created vehicle \'1234\' (Scorpio, Status: AUTHORIZED)','127.0.0.1'),(2,'2026-10-07 17:31:24',1,'tiger','DRIVER_CREATE',NULL,NULL,'Created Driver profile: \'Yawar Ramzan wani\' (563753656TTTT121121212, Hill Driving: YES, Status: AUTHORIZED)','127.0.0.1'),(3,'2026-10-07 17:31:33',1,'tiger','DRIVER_UPDATE',NULL,NULL,'Updated Driver profile: \'Yawar Ramzan wani\' (563, Status: AUTHORIZED)','127.0.0.1'),(4,'2026-10-07 17:31:47',1,'tiger','RFID_ASSIGN',NULL,NULL,'Registered & assigned RFID \'90909090\' to driver \'Yawar Ramzan wani\'','127.0.0.1'),(5,'2026-10-07 17:31:53',1,'tiger','VEHICLE_EXIT','1234',NULL,'Confirmed EXIT (Outbound Dispatch) for 1234 (Scorpio) by tiger','127.0.0.1'),(6,'2026-10-07 17:35:59',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(7,'2026-10-07 17:40:03',1,'tiger','LOGIN',NULL,NULL,'User \'tiger\' logged in successfully (ADMIN)','127.0.0.1'),(8,'2026-10-07 17:40:32',1,'tiger','VEHICLE_ENTRY','1234',NULL,'Confirmed ENTRY (Arrival to Depot) for 1234 (Scorpio) by tiger','127.0.0.1'),(9,'2026-10-07 17:40:56',1,'tiger','VEHICLE_EXIT','1234',NULL,'Confirmed EXIT (Outbound Dispatch) for 1234 (Scorpio) by tiger','127.0.0.1'),(10,'2026-10-07 17:41:23',1,'tiger','VEHICLE_ENTRY','1234',NULL,'Confirmed ENTRY (Arrival to Depot) for 1234 (Scorpio) by tiger','127.0.0.1'),(11,'2026-10-07 17:41:49',1,'tiger','VEHICLE_EXIT','1234',NULL,'Confirmed EXIT (Outbound Dispatch) for 1234 (Scorpio) by tiger','127.0.0.1'),(12,'2026-10-07 17:43:14',1,'tiger','VEHICLE_ENTRY','1234',NULL,'Confirmed ENTRY (Arrival to Depot) for 1234 (Scorpio) by tiger','127.0.0.1');
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
  `camera_id` varchar(64) NOT NULL,
  `camera_name` varchar(120) NOT NULL,
  `role` varchar(16) NOT NULL,
  `rtsp_url` varchar(255) DEFAULT NULL,
  `resolution` varchar(32) DEFAULT NULL,
  `is_enabled` tinyint(1) NOT NULL,
  `last_seen` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_camera_configs_camera_id` (`camera_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `rfid_uid` varchar(32) DEFAULT NULL,
  `vehicle_number` varchar(32) DEFAULT NULL,
  `vehicle_id` int DEFAULT NULL,
  `device_id` int DEFAULT NULL,
  `direction` varchar(16) NOT NULL,
  `reason` varchar(64) NOT NULL,
  `event_id` varchar(64) DEFAULT NULL,
  `operator_id` int DEFAULT NULL,
  `remarks` text,
  `is_demo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `vehicle_id` (`vehicle_id`),
  KEY `device_id` (`device_id`),
  KEY `operator_id` (`operator_id`),
  KEY `ix_denied_attempts_event_id` (`event_id`),
  KEY `ix_denied_attempts_vehicle_number` (`vehicle_number`),
  KEY `ix_denied_attempts_timestamp` (`timestamp`),
  KEY `ix_denied_attempts_reason` (`reason`),
  KEY `ix_denied_attempts_rfid_uid` (`rfid_uid`),
  CONSTRAINT `denied_attempts_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`),
  CONSTRAINT `denied_attempts_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `denied_attempts_ibfk_3` FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `denied_attempts`
--

LOCK TABLES `denied_attempts` WRITE;
/*!40000 ALTER TABLE `denied_attempts` DISABLE KEYS */;
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
  `event_type` varchar(32) NOT NULL,
  `event_id` varchar(64) DEFAULT NULL,
  `raw_payload` text,
  `response_summary` varchar(255) DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_device_events_device_id` (`device_id`),
  KEY `ix_device_events_timestamp` (`timestamp`),
  KEY `ix_device_events_event_id` (`event_id`),
  CONSTRAINT `device_events_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `device_events`
--

LOCK TABLES `device_events` WRITE;
/*!40000 ALTER TABLE `device_events` DISABLE KEYS */;
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
  `device_id` varchar(64) NOT NULL,
  `device_name` varchar(120) NOT NULL,
  `device_type` varchar(32) NOT NULL,
  `gate` varchar(64) NOT NULL,
  `direction` varchar(16) NOT NULL,
  `ip_address` varchar(64) DEFAULT NULL,
  `status` varchar(16) NOT NULL,
  `last_seen` datetime DEFAULT NULL,
  `last_event` varchar(255) DEFAULT NULL,
  `firmware_version` varchar(32) DEFAULT NULL,
  `api_key_hash` varchar(256) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_devices_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devices`
--

LOCK TABLES `devices` WRITE;
/*!40000 ALTER TABLE `devices` DISABLE KEYS */;
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
  `name` varchar(120) NOT NULL,
  `armynumber` varchar(64) DEFAULT NULL,
  `driver_rank` varchar(64) DEFAULT NULL,
  `company` varchar(64) DEFAULT NULL,
  `section` varchar(64) DEFAULT NULL,
  `hill_driving` varchar(10) NOT NULL,
  `auth_status` varchar(32) NOT NULL,
  `authorized_vehicle_types` text,
  `license_number` varchar(64) DEFAULT NULL,
  `mobile_number` varchar(24) DEFAULT NULL,
  `designation` varchar(64) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `remarks` text,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `rfid_uid` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_drivers_armynumber` (`armynumber`),
  KEY `ix_drivers_is_active` (`is_active`),
  KEY `ix_drivers_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `drivers`
--

LOCK TABLES `drivers` WRITE;
/*!40000 ALTER TABLE `drivers` DISABLE KEYS */;
INSERT INTO `drivers` VALUES (1,'Yawar Ramzan wani','563','NK','1 company','MT','YES','AUTHORIZED','LRV','46094680480','07006014310','NK',1,NULL,'2026-10-07 17:31:24','2026-10-07 17:31:47','90909090');
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
  `uid` varchar(32) NOT NULL,
  `vehicle_id` int DEFAULT NULL,
  `card_status` varchar(32) NOT NULL,
  `assigned_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `remarks` text,
  `is_demo` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `driver_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_rfid_cards_uid` (`uid`),
  KEY `ix_rfid_cards_vehicle_id` (`vehicle_id`),
  KEY `ix_rfid_cards_card_status` (`card_status`),
  KEY `fk_rfid_cards_driver` (`driver_id`),
  CONSTRAINT `fk_rfid_cards_driver` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`) ON DELETE SET NULL,
  CONSTRAINT `rfid_cards_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rfid_cards`
--

LOCK TABLES `rfid_cards` WRITE;
/*!40000 ALTER TABLE `rfid_cards` DISABLE KEYS */;
INSERT INTO `rfid_cards` VALUES (1,'90909090',NULL,'ACTIVE','2026-10-07','2026-11-07',NULL,0,'2026-10-07 17:31:47','2026-10-07 17:31:47',1);
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
  `key` varchar(64) NOT NULL,
  `value` text NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_system_settings_key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_settings`
--

LOCK TABLES `system_settings` WRITE;
/*!40000 ALTER TABLE `system_settings` DISABLE KEYS */;
INSERT INTO `system_settings` VALUES (1,'system_name','Smart RFID + ANPR Vehicle Gate System','Display name of the application','2026-10-07 17:29:22'),(2,'gate_direction_mode','ENTRY_ONLY','Default direction mode','2026-10-07 17:29:22'),(3,'scan_cooldown_seconds','3','Cooldown duration between scans for same RFID in seconds','2026-10-07 17:29:22'),(4,'device_heartbeat_timeout','35','Seconds before an inactive device is marked OFFLINE','2026-10-07 17:29:22'),(5,'barrier_auto_close_delay','4','Seconds to simulate barrier gate open before auto-closing','2026-10-07 17:29:22'),(6,'anpr_confidence_threshold','80.0','Minimum confidence score (%) for ANPR auto-match','2026-10-07 17:29:22'),(7,'dashboard_refresh_interval','5','Dashboard auto-refresh interval in seconds','2026-10-07 17:29:22'),(8,'demo_mode_enabled','0','Whether simulated demo controls and quick actions are shown','2026-10-07 17:29:22');
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
  `username` varchar(64) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  `full_name` varchar(120) NOT NULL,
  `email` varchar(120) DEFAULT NULL,
  `role` varchar(32) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'tiger','scrypt:32768:8:1$DscGnmZEqwpjhGrN$c222d97e5132ffb10080443e356473ccdee418b07f5247439a09051f770ca5df47223df3d5a2d1a14bc8b1f65d13777ed024670f27277a4622fa8d732d62a6e9','tiger',NULL,'ADMIN',1,'2026-10-03 13:04:21','2026-10-07 17:40:03'),(2,'maingate','scrypt:32768:8:1$KFv9Umxbkvk038Nr$d8df59afc983994e425ffb49665d37ed2fdc1faf68a2ccc292803f78dab069493d039b735b4ae4608206bdbb1246e750cdfd82a268fae90fa62533ca4301fc3c','Main Gate Operator','maingate@depot.local','MAINGATE',1,'2026-10-06 07:40:13','2026-10-07 17:11:47');
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
  `driver_name` varchar(120) DEFAULT NULL,
  `entry_time` datetime NOT NULL,
  `entry_device_id` int DEFAULT NULL,
  `entry_operator_id` int DEFAULT NULL,
  `exit_time` datetime DEFAULT NULL,
  `exit_device_id` int DEFAULT NULL,
  `exit_operator_id` int DEFAULT NULL,
  `duration_seconds` int DEFAULT NULL,
  `status` varchar(32) NOT NULL,
  `direction` varchar(16) NOT NULL,
  `is_manual` tinyint(1) NOT NULL,
  `manual_reason` varchar(255) DEFAULT NULL,
  `remarks` text,
  `is_demo` tinyint(1) NOT NULL,
  `entry_event_id` varchar(64) DEFAULT NULL,
  `exit_event_id` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `entry_device_id` (`entry_device_id`),
  KEY `entry_operator_id` (`entry_operator_id`),
  KEY `exit_device_id` (`exit_device_id`),
  KEY `exit_operator_id` (`exit_operator_id`),
  KEY `ix_vehicle_movements_exit_time` (`exit_time`),
  KEY `ix_vehicle_movements_driver_id` (`driver_id`),
  KEY `ix_vehicle_movements_entry_time` (`entry_time`),
  KEY `ix_vehicle_movements_status` (`status`),
  KEY `ix_vehicle_movements_rfid_card_id` (`rfid_card_id`),
  KEY `ix_vehicle_movements_entry_event_id` (`entry_event_id`),
  KEY `ix_vehicle_movements_exit_event_id` (`exit_event_id`),
  KEY `ix_vehicle_movements_vehicle_id` (`vehicle_id`),
  CONSTRAINT `vehicle_movements_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_2` FOREIGN KEY (`rfid_card_id`) REFERENCES `rfid_cards` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_3` FOREIGN KEY (`entry_device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_4` FOREIGN KEY (`entry_operator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_5` FOREIGN KEY (`exit_device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `vehicle_movements_ibfk_6` FOREIGN KEY (`exit_operator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicle_movements`
--

LOCK TABLES `vehicle_movements` WRITE;
/*!40000 ALTER TABLE `vehicle_movements` DISABLE KEYS */;
INSERT INTO `vehicle_movements` VALUES (1,1,1,1,'Yawar Ramzan wani','2026-10-07 17:40:32',NULL,1,'2026-10-07 17:31:53',NULL,1,519,'INSIDE','EXIT',0,NULL,'',0,NULL,NULL,'2026-10-07 17:31:53'),(2,1,1,1,'Yawar Ramzan wani','2026-10-07 17:41:23',NULL,1,'2026-10-07 17:40:56',NULL,1,26,'INSIDE','EXIT',0,NULL,'',0,NULL,NULL,'2026-10-07 17:40:56'),(3,1,1,1,'Yawar Ramzan wani','2026-10-07 17:43:14',NULL,1,'2026-10-07 17:41:49',NULL,1,84,'INSIDE','EXIT',0,NULL,'',0,NULL,NULL,'2026-10-07 17:41:49');
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
  `registration_number` varchar(32) NOT NULL,
  `vehicle_type` varchar(32) NOT NULL,
  `issue_date` date DEFAULT NULL,
  `custodian_name` varchar(120) DEFAULT NULL,
  `armynumber` varchar(64) DEFAULT NULL,
  `mobile_number` varchar(24) DEFAULT NULL,
  `auth_status` varchar(32) NOT NULL,
  `current_vehicle_location` varchar(20) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_demo` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_vehicles_registration_number` (`registration_number`),
  KEY `ix_vehicles_auth_status` (`auth_status`),
  KEY `ix_vehicles_current_vehicle_location` (`current_vehicle_location`),
  KEY `ix_vehicles_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicles`
--

LOCK TABLES `vehicles` WRITE;
/*!40000 ALTER TABLE `vehicles` DISABLE KEYS */;
INSERT INTO `vehicles` VALUES (1,'1234','Scorpio','2026-09-28','Virat Kohli','563753656TTTT','07006014310','AUTHORIZED','INSIDE',1,0,'2026-10-07 17:30:58','2026-10-07 17:43:14');
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

-- Dump completed on 2026-10-07 23:14:17
