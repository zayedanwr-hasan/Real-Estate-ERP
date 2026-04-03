BEGIN;

-- 1) Snapshot rows that are candidates for deletion.
CREATE TABLE IF NOT EXISTS finance.accounts_legacy_individual_backup AS
SELECT a.*
FROM finance.accounts a
WHERE 1 = 0;

INSERT INTO finance.accounts_legacy_individual_backup
SELECT a.*
FROM finance.accounts a
WHERE COALESCE(a.is_active, true) = true
  AND (
    EXISTS (
      SELECT 1
      FROM finance.vendors v
      WHERE LOWER(TRIM(v.vendor_name)) = LOWER(TRIM(a.account_name))
    )
    OR EXISTS (
      SELECT 1
      FROM finance.customers c
      WHERE LOWER(TRIM(c.customer_name)) = LOWER(TRIM(a.account_name))
    )
  )
  AND TRIM(a.account_code) NOT IN ('1104', '2101');

-- 2) Soft-disable first (safer rollback path).
UPDATE finance.accounts a
SET is_active = false
WHERE a.account_code IN (
  SELECT b.account_code
  FROM finance.accounts_legacy_individual_backup b
);

-- 3) Hard delete only rows that are not referenced anywhere in ledger.
DELETE FROM finance.accounts a
WHERE a.account_code IN (
  SELECT b.account_code
  FROM finance.accounts_legacy_individual_backup b
)
AND NOT EXISTS (
  SELECT 1
  FROM finance.ledger l
  WHERE TRIM(l.account_code) = TRIM(a.account_code)
);

-- 4) Review rows that still cannot be deleted because they are referenced.
--    (Run after COMMIT if needed)
-- SELECT a.account_code, a.account_name
-- FROM finance.accounts a
-- WHERE a.account_code IN (
--   SELECT account_code FROM finance.accounts_legacy_individual_backup
-- )
-- ORDER BY a.account_code;

COMMIT;

