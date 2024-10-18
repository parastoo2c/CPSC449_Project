# CPSC449_Project

## Create Import MySQL Database
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

