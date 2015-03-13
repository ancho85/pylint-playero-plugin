SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `Alotment`
-- ----------------------------
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

-- ----------------------------
-- Table structure for `Deposit`
-- ----------------------------
CREATE TABLE `Deposit` (
`internalId`  int(11) NOT NULL AUTO_INCREMENT ,
`SerNr`  int(11) NULL DEFAULT NULL ,
`ToSerNr`  int(11) NULL DEFAULT NULL ,
`TransDate`  date NULL DEFAULT NULL ,
`TransTime`  time NULL DEFAULT NULL ,
`Office`  varchar(10) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`Computer`  varchar(5) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`Status`  int(11) NULL DEFAULT NULL ,
`User`  varchar(10) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`Shift`  varchar(5) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`Synchronized`  tinyint(1) NULL DEFAULT NULL COMMENT 'boolean' ,
`Printed`  tinyint(1) NULL DEFAULT NULL COMMENT 'boolean' ,
`Invalid`  tinyint(1) NULL DEFAULT NULL COMMENT 'boolean' ,
`Labels`  varchar(50) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'set' ,
`ShiftDate`  date NULL DEFAULT NULL ,
`Currency`  varchar(3) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`BaseRate1`  double NULL DEFAULT NULL ,
`BaseRate2`  double NULL DEFAULT NULL ,
`FromRate`  double NULL DEFAULT NULL ,
`ToBaseRate1`  double NULL DEFAULT NULL ,
`ToBaseRate2`  double NULL DEFAULT NULL ,
`BaseRate`  double NULL DEFAULT NULL ,
`CurrencyRate`  double NULL DEFAULT NULL ,
`Comment`  varchar(60) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`Total`  double NULL DEFAULT NULL ,
`Cash`  double NULL DEFAULT NULL ,
`CashReg`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`FinIdent`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`OperationType`  int(11) NULL DEFAULT NULL ,
`Commision`  double NULL DEFAULT NULL ,
`Department`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`PosEventNr`  int(11) NULL DEFAULT NULL ,
`PrintedTimes`  int(11) NULL DEFAULT NULL ,
`attachFlag`  tinyint(1) NULL DEFAULT NULL COMMENT 'boolean' ,
`syncVersion`  int(11) NULL DEFAULT NULL ,
`InvoiceNr`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`TaxRegNr`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL COMMENT 'string' ,
`OriginNr`  int(11) NULL DEFAULT NULL ,
`OriginType`  int(11) NULL DEFAULT NULL ,
`CustName`  varchar(60) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
`CustCode`  varchar(20) CHARACTER SET latin1 COLLATE latin1_general_cs NULL DEFAULT NULL ,
PRIMARY KEY (`internalId`)
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=latin1 COLLATE=latin1_general_cs

;

-- ----------------------------
-- Indexes structure for table Deposit
-- ----------------------------
CREATE UNIQUE INDEX `ToSerNr` USING BTREE ON `Deposit`(`ToSerNr`) ;
CREATE UNIQUE INDEX `SerNr` USING BTREE ON `Deposit`(`SerNr`) ;
CREATE INDEX `Office` USING BTREE ON `Deposit`(`Office`, `Computer`, `SerNr`, `internalId`) ;
CREATE INDEX `StatusTransDate` USING BTREE ON `Deposit`(`Status`, `TransDate`, `internalId`) ;
CREATE INDEX `ShiftDate` USING BTREE ON `Deposit`(`ShiftDate`, `internalId`) ;
CREATE INDEX `InvoiceNr` USING BTREE ON `Deposit`(`InvoiceNr`, `internalId`) ;
CREATE INDEX `OriginNr` USING BTREE ON `Deposit`(`OriginType`, `OriginNr`, `internalId`) ;
CREATE INDEX `OfficeShiftDate` USING BTREE ON `Deposit`(`Office`, `ShiftDate`, `internalId`) ;
CREATE INDEX `TransDate` USING BTREE ON `Deposit`(`TransDate`, `internalId`) ;
CREATE INDEX `CustCode` USING BTREE ON `Deposit`(`CustCode`, `internalId`) ;

-- ----------------------------
-- Function structure for `convertToBase`
-- ----------------------------
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `convertToBase`(fromCurrency VARCHAR(20), amount DOUBLE, curRate DOUBLE, baseRate DOUBLE, base INT) RETURNS double
    READS SQL DATA
BEGIN
            DECLARE base1ToFactor, base1FrFactor, base1ConvertionDirection, base1RoundOff INT;
            DECLARE base2ToFactor, base2FrFactor, base2ConvertionDirection, base2RoundOff INT;
            DECLARE toFactr, frFactr, converBase, direction, roundOf INT;
            DECLARE base1Amount, base2Amount, res DOUBLE;
            DECLARE base1, base2 VARCHAR(20);

            SELECT BaseCur1, BaseCur2
            INTO base1, base2
            FROM OurSettings;

            SELECT ToFactor, FrFactor, ConvertionDirection, RoundOff
            INTO base1ToFactor, base1FrFactor, base1ConvertionDirection, base1RoundOff
            FROM Currency WHERE Code = base1
            COLLATE latin1_general_cs;

            SELECT ToFactor, FrFactor, ConvertionDirection, RoundOff
            INTO base2ToFactor, base2FrFactor, base2ConvertionDirection, base2RoundOff
            FROM Currency WHERE Code = base2
            COLLATE latin1_general_cs;

            IF fromCurrency = base1 THEN
                set base1Amount = amount; -- base1Amount = round(amount,self.RoundOff)
                set base2Amount = resolve(amount,baseRate,base2ToFactor,base2FrFactor,abs(base2ConvertionDirection-1)); -- invierto direccion
                -- r2 = round(res,base2.RoundOff)
            ELSEIF fromCurrency = base2 THEN
                set base2Amount = amount; -- base2Amount = round(amount,base2RoundOff)
                set base1Amount = resolve(amount,baseRate,base2ToFactor,base2FrFactor,base2ConvertionDirection);
                -- r1 = round(res,base1.RoundOff)
            ELSE
                SELECT ConvertionBase, ConvertionDirection, ToFactor, FrFactor,RoundOff
                INTO converBase, direction, toFactr, frFactr, roundOf
                FROM Currency
                WHERE Code = fromCurrency
                COLLATE latin1_general_cs;

                IF converBase = 0 THEN
                    set base1Amount = resolve(amount,curRate,toFactr,frFactr,direction);
                    set res = resolve(base1Amount,baseRate,base1ToFactor,base1FrFactor,abs(base1ConvertionDirection-1)); -- invierto direccion CAG
                    set base2Amount = round(res,base2RoundOff);
                ELSE
                    set base2Amount = resolve(amount,curRate,toFactr,frFactr,direction);
                    set res = resolve(base2Amount,baseRate,base2ToFactor,base2FrFactor,base2ConvertionDirection);
                    set base1Amount = round(res,base1RoundOff);
                END IF;
            END IF;

            IF base = 1 THEN
                RETURN base1Amount;
            ELSEIF base = 2 THEN
                RETURN base2Amount;
            END IF;
        END
;;
DELIMITER ;

-- ----------------------------
-- Function structure for `resolve`
-- ----------------------------
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `resolve`(a DOUBLE, b DOUBLE, f1 DOUBLE, f2 DOUBLE, direction INT) RETURNS double
BEGIN
            DECLARE factor DOUBLE;
            SET factor = 0.0;
            IF f2 THEN
                SET factor = f1 / f2;
            END IF;

            IF (direction = 1) THEN
                IF b THEN
                   RETURN (a / b) * factor;
                ELSE
                   RETURN 0;
                END IF;
            ELSE
                RETURN (a * b) * factor;
            END IF;
        END
;;
