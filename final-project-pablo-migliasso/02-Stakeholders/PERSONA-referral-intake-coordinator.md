# Persona: referral intake coordinator

## Goals and measures

Create accurate Caregate referral records from incoming documents and route each patient to the correct
specialty, site, and urgency path. The error rate is unknown; incorrect keying can send a patient to the
wrong destination or create downstream authorization rework [B4.2].

## Tools and working environment

RightFax, Caregate, partner/payer portals, phone, and a personally maintained lookup sheet with
approximately **900 rows (reported)** mapping fax numbers to referring practices [B4.2, B7]. **62% of
5,800 monthly referrals (measured)** arrive by fax [B9].

## Top pains

1. Re-keying document fields into Caregate.
2. Poor fax quality and missing insurance data.
3. Urgency depends on human interpretation because forms are inconsistent.

## AI literacy and attitude

No direct usage evidence was captured. The coordinator supports automation of typing while retaining final
verification and urgency judgment. His playback statement defines the target control model: machine-prepared
fields with human review [B8].

## Design implication

Use extraction as augmentation. The pilot should flag illegibility, absent required fields, conflicting
identifiers, and clinical urgency for human review instead of guessing.
