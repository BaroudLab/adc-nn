-- -- SQLite
-- SELECT name, email FROM users;
-- SELECT id, name, user_id, date from features;
-- SELECT DISTINCT date FROM datasets WHERE antibiotic_type='Tetracycline';
-- .tables
-- -- .schema

-- SELECT  chips.id, datasets.path, chips.stack_index
-- FROM datasets 
-- JOIN chips 
-- ON chips.dataset_id = datasets.id;

SELECT * FROM droplets ORDER BY id DESC LIMIT 10;

-- INSERT INTO features (name, user_id, date) VALUES ("bad alignment", 1, CURRENT_DATE);
-- INSERT INTO features (name, user_id, date) VALUES ("planktonic", 1, CURRENT_DATE);

SELECT * from features;
-- DELETE FROM features WHERE name="planktonic";
-- SELECT * from features;


SELECT features.id, features.name, COUNT(droplets.feature_id) 
FROM features 
JOIN droplets 
ON features.id = droplets.feature_id 
GROUP BY features.id;



-- SELECT  chips.concentration, datasets.unit, datasets.path
-- FROM datasets 
-- JOIN chips 
-- ON chips.dataset_id = datasets.id
-- WHERE 
-- datasets.antibiotic_type='Cirpofloxacin' AND
-- datasets.date='2022-05-31';

-- SELECT datasets.id,
-- datasets.date,
-- datasets.antibiotic_type,
-- chips.stack_index,
-- chips.concentration,
-- datasets.unit,
-- datasets.path
-- FROM datasets 
-- JOIN chips 
-- ON chips.dataset_id = datasets.id
-- WHERE datasets.antibiotic_type='Tetracycline';


-- SELECT id
-- FROM chips
-- WHERE dataset_id="454cf636c8964414b77962f1d3df2ab6";