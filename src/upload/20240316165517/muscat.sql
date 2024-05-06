-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: database-1.cro2kqu2go52.eu-north-1.rds.amazonaws.com
-- Generation Time: Mar 12, 2024 at 07:58 AM
-- Server version: 10.11.6-MariaDB-log
-- PHP Version: 8.1.27

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `muscat`
--

-- --------------------------------------------------------

--
-- Table structure for table `company`
--

CREATE TABLE `company` (
  `id` int(11) NOT NULL,
  `register_num` varchar(20) DEFAULT NULL,
  `company_name` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `company`
--

INSERT INTO `company` (`id`, `register_num`, `company_name`) VALUES
(19, 'ㅈㅈㅈㅈ', 'ㅈ'),
(26, '22', '22'),
(27, 'lll', 'lll'),
(28, '111', '1123'),
(29, '66666', '65');

-- --------------------------------------------------------

--
-- Table structure for table `notice`
--

CREATE TABLE `notice` (
  `id` int(11) NOT NULL,
  `project_id` int(11) DEFAULT NULL,
  `title` varchar(45) DEFAULT NULL,
  `content` mediumtext DEFAULT NULL,
  `create_by` varchar(45) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `views` int(11) DEFAULT NULL,
  `attachment` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `notice`
--

INSERT INTO `notice` (`id`, `project_id`, `title`, `content`, `create_by`, `create_time`, `views`, `attachment`) VALUES
(1, 1, '1', '1', '1', '2024-03-11 20:39:32', 0, 'muscat.sql'),
(4, 1, '111', '11', '111', '2024-03-12 07:17:04', 0, '0.jpg');

-- --------------------------------------------------------

--
-- Table structure for table `project`
--

CREATE TABLE `project` (
  `id` int(11) NOT NULL,
  `year` int(11) DEFAULT NULL,
  `name` varchar(45) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `checklist_id` int(11) DEFAULT NULL,
  `privacy_type` int(11) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `create_from` date DEFAULT NULL,
  `create_to` date DEFAULT NULL,
  `self_check_from` date DEFAULT NULL,
  `self_check_to` date DEFAULT NULL,
  `imp_check_from` date DEFAULT NULL,
  `imp_check_to` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `project`
--

INSERT INTO `project` (`id`, `year`, `name`, `user_id`, `checklist_id`, `privacy_type`, `created_date`, `create_from`, `create_to`, `self_check_from`, `self_check_to`, `imp_check_from`, `imp_check_to`) VALUES
(1, 123, 'project1', 12, 12, 1, '2024-03-11 17:24:27', '2024-03-01', '2024-03-23', '2024-03-01', '2024-03-10', '2024-03-02', '2024-03-03'),
(3, 0, 'string', 0, 0, 0, '2024-03-11 17:55:41', '2024-03-11', '2024-03-11', '2024-03-11', '2024-03-11', '2024-03-11', '2024-03-11');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `user_id` int(11) NOT NULL,
  `user_email` varchar(100) NOT NULL,
  `user_password` varchar(100) NOT NULL,
  `user_type` int(11) NOT NULL,
  `company_name` varchar(100) DEFAULT NULL,
  `register_num` varchar(45) DEFAULT NULL,
  `company_address` varchar(100) DEFAULT NULL,
  `manager_name` varchar(45) DEFAULT NULL,
  `manager_phone` varchar(45) DEFAULT NULL,
  `manager_depart` varchar(45) DEFAULT NULL,
  `manager_grade` varchar(45) DEFAULT NULL,
  `other` varchar(45) DEFAULT NULL,
  `approval` int(11) DEFAULT NULL,
  `nickname` varchar(45) DEFAULT NULL,
  `admin_name` varchar(45) DEFAULT NULL,
  `admin_phone` varchar(45) DEFAULT NULL,
  `code` varchar(45) DEFAULT NULL,
  `updated_time` datetime DEFAULT NULL,
  `access_time` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`user_id`, `user_email`, `user_password`, `user_type`, `company_name`, `register_num`, `company_address`, `manager_name`, `manager_phone`, `manager_depart`, `manager_grade`, `other`, `approval`, `nickname`, `admin_name`, `admin_phone`, `code`, `updated_time`, `access_time`) VALUES
(2, 'string', 'ecb252044b5ea0f679ee78ec1a12904739e2904d', 1, 'string', 'string', 'string', 'string', 'string', 'string', 'string', 'string', 1, 'string', 'string', 'string', NULL, NULL, '2024-03-11 19:38:22'),
(3, 'ayong19910110@gmail.com', '86f7e437faa5a7fce15d1ddcb9eaeaea377667b8', 0, NULL, '', '', '', '', '', '', '', 0, 'SupperAdmin', '', '', '75566544', '2024-03-11 19:38:22', '2024-03-11 19:38:22'),
(4, '111', 'ecb252044b5ea0f679ee78ec1a12904739e2904d', 0, NULL, 'string', 'string', 'string', 'string', 'string', 'string', 'string', 0, '111', 'string', 'string', NULL, NULL, '2024-03-12 03:26:28');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `company`
--
ALTER TABLE `company`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `notice`
--
ALTER TABLE `notice`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `project`
--
ALTER TABLE `project`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `company`
--
ALTER TABLE `company`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30;

--
-- AUTO_INCREMENT for table `notice`
--
ALTER TABLE `notice`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `project`
--
ALTER TABLE `project`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
