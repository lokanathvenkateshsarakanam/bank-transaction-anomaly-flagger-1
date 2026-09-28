      *================================================================*
      * PROGRAM: FRAUDSCR.cbl                                          *
      * PURPOSE: CORE BANKING MAINFRAME TRANSACTION ANOMALY SCREENER   *
      * SYSTEM : GLOBAL SETTLEMENT & CLEARING BATCH (IBM z/OS CICS)    *
      * AUTHOR : ENTERPRISE RISK ENGINE                                *
      *================================================================*
       IDENTIFICATION DIVISION.
       PROGRAM-ID. FRAUDSCR.
       AUTHOR. RISK-ENGINE.
       DATE-WRITTEN. 2026-09-28.

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-Z16.
       OBJECT-COMPUTER. IBM-Z16.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
      *----------------------------------------------------------------*
      * INCOMING MAINFRAME TRANSACTION RECORD (80-BYTE FIXED FORMAT)   *
      *----------------------------------------------------------------*
       01  WS-TRANSACTION-RECORD.
           05  WS-TXN-ID               PIC X(18).
           05  WS-SENDER-ACCT          PIC X(12).
           05  WS-RECEIVER-ACCT        PIC X(12).
           05  WS-TXN-AMOUNT           PIC 9(7)V99 COMP-3.
           05  WS-HIST-AVG-AMT         PIC 9(7)V99 COMP-3.
           05  WS-DEVICE-STATUS        PIC X(04).
               88 DEV-KNOWN            VALUE 'BASE'.
               88 DEV-NEW              VALUE 'NEW '.
           05  WS-LOCATION-FLAG        PIC X(04).
               88 LOC-DOMESTIC         VALUE 'DOM '.
               88 LOC-FOREIGN          VALUE 'FORG'.
           05  WS-BLACKLIST-STATUS     PIC X(01).
               88 ACCT-CLEAN           VALUE '0'.
               88 ACCT-BLACKLISTED     VALUE '1'.

      *----------------------------------------------------------------*
      * MAINFRAME SCREENING DECISION & RISK SCORING REGISTERS          *
      *----------------------------------------------------------------*
       01  WS-SCREENING-OUTPUT.
           05  WS-DECISION             PIC X(20) VALUE 'APPROVE'.
           05  WS-RISK-SCORE           PIC 9V999 VALUE 0.020.
           05  WS-FLAG-REASON          PIC X(30) VALUE 'NONE'.
           05  WS-CALC-THRESHOLD       PIC 9(7)V99 COMP-3.

       PROCEDURE DIVISION.
       0000-MAIN-LOGIC.
           PERFORM 1000-INITIALIZE.
           PERFORM 2000-EVALUATE-RULES.
           PERFORM 3000-GENERATE-DECISION.
           GOBACK.

       1000-INITIALIZE.
           MOVE 'APPROVE' TO WS-DECISION.
           MOVE 0.020     TO WS-RISK-SCORE.
           MOVE 'CLEAN'   TO WS-FLAG-REASON.
      * Compute 3x baseline threshold for Propositional Rule Check
           MULTIPLY WS-HIST-AVG-AMT BY 3 GIVING WS-CALC-THRESHOLD.

       2000-EVALUATE-RULES.
      * Rule 1: Check Blacklist (ADSA 0-Hop Risk)
           IF ACCT-BLACKLISTED
               MOVE 'FREEZE_ACCOUNT' TO WS-DECISION
               MOVE 0.950 TO WS-RISK-SCORE
               MOVE 'RULE-BLACKLIST-CONFIRMED' TO WS-FLAG-REASON
               EXIT PARAGRAPH
           END-IF.

      * Rule 2: Propositional Logic Account Takeover Check (DMGT U1)
      * Formula: (P_HIGH_AMOUNT AND P_NEW_DEVICE) -> FLAG_ATO
           IF WS-TXN-AMOUNT > WS-CALC-THRESHOLD AND DEV-NEW
               MOVE 'FLAG_MANUAL_REVIEW' TO WS-DECISION
               MOVE 0.370 TO WS-RISK-SCORE
               MOVE 'RULE-ATO-NEW-DEVICE-BURST' TO WS-FLAG-REASON
               EXIT PARAGRAPH
           END-IF.

      * Rule 3: Currency Transaction Reporting (CTR $10,000 threshold)
           IF WS-TXN-AMOUNT >= 10000.00
               MOVE 'FLAG_MANUAL_REVIEW' TO WS-DECISION
               MOVE 0.250 TO WS-RISK-SCORE
               MOVE 'RULE-CTR-REGULATORY-LIMIT' TO WS-FLAG-REASON
               EXIT PARAGRAPH
           END-IF.

       3000-GENERATE-DECISION.
           DISPLAY 'MAINFRAME TRANSACTION AUDIT RECORD'
           DISPLAY 'TXN ID      : ' WS-TXN-ID
           DISPLAY 'DECISION    : ' WS-DECISION
           DISPLAY 'RISK SCORE  : ' WS-RISK-SCORE
           DISPLAY 'FLAG REASON : ' WS-FLAG-REASON.
