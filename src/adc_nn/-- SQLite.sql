-- SQLite
SELECT name, email FROM users;
SELECT id, name, user_id, date from features;
SELECT DISTINCT date FROM datasets WHERE antibiotic_type='Tetracycline';
.tables
-- .schema

SELECT * FROM droplets;

SELECT * FROM features;


SELECT  chips.concentration, datasets.unit, datasets.path
FROM datasets 
JOIN chips 
ON chips.dataset_id = datasets.id
WHERE 
datasets.antibiotic_type='Cirpofloxacin' AND
datasets.date='2022-05-31';

SELECT datasets.id,
datasets.date,
datasets.antibiotic_type,
chips.stack_index,
chips.concentration,
datasets.unit,
datasets.path
FROM datasets 
JOIN chips 
ON chips.dataset_id = datasets.id
WHERE datasets.antibiotic_type='Tetracycline';


SELECT id
FROM chips
WHERE dataset_id="454cf636c8964414b77962f1d3df2ab6";