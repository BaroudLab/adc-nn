-- SQLite
SELECT name, email FROM users;
SELECT name, user_id, date from features;
SELECT DISTINCT date FROM datasets WHERE antibiotic_type='Tetracycline';
-- .tables
-- .schema

SELECT  chips.concentration, datasets.path
FROM datasets 
JOIN chips 
ON chips.dataset_id = datasets.id
WHERE 
datasets.antibiotic_type='Tetracycline' AND
datasets.date='2023-04-04';

SELECT datasets.id,
datasets.date,
datasets.antibiotic_type,
chips.chip_id,
chips.concentration,
datasets.unit,
datasets.path
FROM datasets 
JOIN chips 
ON chips.dataset_id = datasets.id
WHERE datasets.antibiotic_type='Tetracycline';

SELECT datasets.id,
datasets.date,
datasets.antibiotic_type,
chips.chip_id,
chips.concentration,
datasets.unit,
datasets.path
FROM datasets 
JOIN chips 
ON chips.dataset_id = datasets.id
WHERE datasets.antibiotic_type=;