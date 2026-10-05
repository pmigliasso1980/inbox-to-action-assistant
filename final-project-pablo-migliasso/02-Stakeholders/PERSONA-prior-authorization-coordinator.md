# Persona: prior authorization coordinator

## Goals and measures

Move authorization requests to payer decisions quickly enough that patients receive scheduled care and
claims contain valid authorization. Formal measures were not supplied; observed behavior shows that open
requests, chase dates, and missing documentation drive the day [B3.1, B4.1].

## Tools and working environment

Caregate orders, seven payer portals, phone, RightFax, payer-policy PDFs, and a desktop Excel tracker with
**431 open rows (measured)** and **14 columns (measured)** at observation [B4.1, B7]. The tracker contains
approximately **12 years of reported** payer rules and workarounds [B4.1].

## Top pains

1. Status chasing consumes much of the day, including payer hold time.
2. Missing clinic documentation introduces unpredictable waits of **one day to one week (reported)**.
3. Critical payer knowledge and open-work status live in personal spreadsheets.

## AI literacy and attitude

The observed coordinator had not used AI because the work contains PHI and no approved destination exists.
She wants automation for every chase but explicitly retains clinical judgment about supporting documents.
Her desired outcome is operational resilience: taking a holiday without the tracker stopping [B3.1, B8].

## Design implication

Start with read-only aggregation and exception surfacing. Do not automate clinical-document sufficiency or
payer submission until policy, access, and audit controls exist.
