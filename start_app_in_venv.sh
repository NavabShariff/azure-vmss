   #!/bin/bash

   # Source the virtual environment activation script
   source /opt/my_flask_app/venv/bin/activate

   # Execute the Flask application using the venv's python
   exec python3 /opt/my_flask_app/app.py
   