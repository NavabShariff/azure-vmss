
### **Part 3: Local Testing Steps**

Follow these steps to get your Flask app running locally and connected to your Docker MySQL.

1.  **Create the directory structure:**
    * Create a folder named `my_flask_app`.
    * Inside `my_flask_app`, create a folder named `templates`.
    * Place `app.py` directly inside `my_flask_app`.
    * Place `requirements.txt` directly inside `my_flask_app`.
    * Place `index.html` inside the `templates` folder.

2.  **Start your local MySQL database:**
    * Open your terminal.
    * Run the Docker command:
        ```bash
docker run --name local-mysql -e MYSQL_ROOT_PASSWORD=admin123 -e MYSQL_DATABASE=userdata_db -p 3306:3306 -d mysql:8.0
        ```
    * Wait a few moments for the MySQL container to fully start. You can check its status with `docker ps`.

3.  **Set up your Python environment and install dependencies:**
    * Navigate to your `my_flask_app` directory in the terminal:
        ```bash
        cd my_flask_app
        ```
    * (Optional, but highly recommended) Create a Python virtual environment:
        ```bash
        python3 -m venv venv
        ```
    * Activate the virtual environment:
        ```bash
        source venv/bin/activate
        ```
        (On Windows, it might be `venv\Scripts\activate`)
    * Install the required Python packages:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Run your Flask web app:**
    * From within the `my_flask_app` directory and with the virtual environment activated, run:
        ```bash
        python app.py
        ```
    * You should see output similar to: `* Running on http://0.0.0.0:5000/`

5.  **Test the web app in your browser:**
    * Open your web browser and go to: `http://127.0.0.1:5000/`
    * You should see the "My Flask App - V1" heading and the user data submission form.
    * Fill out the form and click "Submit Data". You should see a success message.

6.  **Verify data in MySQL (Optional):**
    * Open a new terminal window (don't close the one running Flask).
    * Connect to your Docker MySQL container:
        ```bash
        docker exec -it local-mysql mysql -h 127.0.0.1 -u root -padmin123 userdata_db
        ```
    * Once connected, run a SQL query to see the data:
        ```sql
        SELECT * FROM users;
        ```
        You should see the data you submitted through the web form.
    * Type `exit` to leave the MySQL prompt.