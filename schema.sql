DROP TABLE IF EXISTS  datasets;
DROP TABLE IF EXISTS  chips; 
DROP TABLE IF EXISTS  features;
DROP TABLE IF EXISTS  droplets;
DROP TABLE IF EXISTS  users;

CREATE TABLE datasets (
  id CHAR(32) PRIMARY KEY ,
  path VARCHAR(255) NOT NULL,
  date DATE NOT NULL,
  antibiotic_type VARCHAR(50) NOT NULL,
  unit VARCHAR(5)
);

CREATE TABLE chips (
  id CHAR(32) PRIMARY KEY ,
  dataset_id CHAR(32) NOT NULL,
  chip_id INT NOT NULL,
  concentration FLOAT NOT NULL,
  FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

CREATE TABLE features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name CHAR NOT NULL,
  user_id INT NOT NULL,
  date CURRENT_DATE,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE droplets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chip_id INT NOT NULL,
  feature_id INT,
  value FLOAT,
  user_id INT,
  date CURRENT_DATE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (chip_id) REFERENCES chips(id),
  FOREIGN KEY (feature_id) REFERENCES features(id)
);


CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name CHAR,
  email CHAR
);