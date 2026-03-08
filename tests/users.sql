-- not null check
SELECT COUNT(*) AS failed_rows
FROM users
WHERE user_id IS NULL;

-- duplicate check
SELECT COUNT(*) AS failed_rows FROM (
  SELECT user_id, COUNT(*)
  FROM users
  GROUP BY user_id
  HAVING COUNT(*) > 1
);
