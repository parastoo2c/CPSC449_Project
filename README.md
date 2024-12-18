# CPSC449_Project

## Group Members
1. Parastoo Toosi CWID 890049349 
2. Elexzandreia Livermore CWID 888823101 
3. Benjamin Nguyen CWID 884523655
4. Chelsea Ogbedeagu CWID 885255463

## Create Container and Install Required Dependencies
1. Create container
    ```bash
    python3 -m venv myenv
    source myenv/bin/activate[in Linux]
    myenv\Scripts\activate [in Windows]
    
2. Install Dependencies
    ```bash
    pip install -r requirements.txt

## Create and Import MySQL Database
To set up the project's database, follow these steps:

1. Ensure you have MySQL installed and running on your system.

2. Open your terminal or command prompt.

3. Create the database:
   ```bash
   mysql -u root -p -e "CREATE DATABASE movie_ratings;"

4. Import the database schema and data
    ```bash
    mysql -u root -p movie_ratings < path/to/movie_ratings.sql

5. When prompted, enter your MySQL root password.

6. Install the packages mentioned in requirements.txt file
    ```bash
    pip install -r requirements.txt

7. Run the following command to list all installed packages and write them to requirements.txt
    ```bash
    pip freeze > requirements.txt
