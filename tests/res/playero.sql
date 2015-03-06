SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `Alotment`
-- ----------------------------
DROP TABLE IF EXISTS `Alotment`;
CREATE TABLE `Alotment` (
`TransTime`  time NULL DEFAULT NULL ,
`ToSerNr`  int(11) NULL DEFAULT NULL ,
`SerNr`  int(11) NULL DEFAULT NULL ,
`ShiftDate`  date NULL DEFAULT NULL ,
`Invalid`  tinyint(1) NULL DEFAULT NULL ,
`Department`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`Status`  int(11) NULL DEFAULT NULL ,
`StartDate`  date NULL DEFAULT NULL ,
`EndDate`  date NULL DEFAULT NULL ,
`attachFlag`  tinyint(1) NULL DEFAULT NULL ,
`DueDays`  int(11) NULL DEFAULT NULL ,
`syncVersion`  int(11) NULL DEFAULT NULL ,
`CustName`  varchar(60) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`Printed`  tinyint(1) NULL DEFAULT NULL ,
`User`  varchar(10) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`PosEventNr`  int(11) NULL DEFAULT NULL ,
`internalId`  int(11) NOT NULL ,
`Shift`  varchar(5) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`OriginNr`  int(11) NULL DEFAULT NULL ,
`OriginType`  int(11) NULL DEFAULT NULL ,
`Comment`  varchar(100) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`TransDate`  date NULL DEFAULT NULL ,
`Office`  varchar(10) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`Synchronized`  tinyint(1) NULL DEFAULT NULL ,
`Labels`  varchar(60) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`Computer`  varchar(5) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`CustCode`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`PrintedTimes`  int(11) NULL DEFAULT NULL ,
PRIMARY KEY (`internalId`)
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=latin1 COLLATE=latin1_general_cs

;

-- ----------------------------
-- Table structure for `AlotmentRow`
-- ----------------------------
DROP TABLE IF EXISTS `AlotmentRow`;
CREATE TABLE `AlotmentRow` (
`RoomType`  varchar(10) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`rowNr`  int(11) NULL DEFAULT NULL ,
`masterId`  int(11) NULL DEFAULT NULL ,
`internalId`  int(11) NOT NULL ,
`Qty`  int(11) NULL DEFAULT NULL ,
PRIMARY KEY (`internalId`)
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=latin1 COLLATE=latin1_general_cs

;

-- ----------------------------
-- Indexes structure for table Alotment
-- ----------------------------
CREATE UNIQUE INDEX `ToSerNr` USING BTREE ON `Alotment`(`ToSerNr`) ;
CREATE UNIQUE INDEX `SerNr` USING BTREE ON `Alotment`(`SerNr`) ;
CREATE INDEX `Office` USING BTREE ON `Alotment`(`Office`, `Computer`, `SerNr`, `internalId`) ;
CREATE INDEX `StatusTransDate` USING BTREE ON `Alotment`(`Status`, `TransDate`, `internalId`) ;
CREATE INDEX `ShiftDate` USING BTREE ON `Alotment`(`ShiftDate`, `internalId`) ;
CREATE INDEX `OriginNr` USING BTREE ON `Alotment`(`OriginType`, `OriginNr`, `internalId`) ;
CREATE INDEX `OfficeShiftDate` USING BTREE ON `Alotment`(`Office`, `ShiftDate`, `internalId`) ;
CREATE INDEX `TransDate` USING BTREE ON `Alotment`(`TransDate`, `internalId`) ;

-- ----------------------------
-- Indexes structure for table AlotmentRow
-- ----------------------------
CREATE INDEX `masterId` USING BTREE ON `AlotmentRow`(`masterId`, `rowNr`, `internalId`) ;
