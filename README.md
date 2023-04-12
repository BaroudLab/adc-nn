# adc-nn
Classification of droplets on anchored chips

* populate database using find_all_datasets notebook (use datasets.json if available)
* symlink database.db into /src/adc-nn
* cd to /src/adc-nn
* flask run
* http://locahost:5000 will show all antibiotics
* http://127.0.0.1:5000/ab/Tetracycline will show all the data as json
* http://127.0.0.1:5000/ab/Tetracycline/2023-04-04/0/4 will show the images (0 is concetnration, 4 is droplet number)


