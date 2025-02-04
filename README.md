# Warning-Dont

## Setting Up a Virtual Environment (venv) in Python

This guide will help you set up a Python virtual environment and run your project inside it.

### Prerequisites
- Install [Python](https://www.python.org/downloads/) (Ensure Python 3.x is installed)
- Install `pip` (comes pre-installed with Python 3.x)

### Steps to Setup and Run

#### 1. Clone the Repository
```sh
git clone https://github.com/vikraman-16/Warning-Dont.git
cd Warning-Dont
```

#### 2. Create a Virtual Environment
```sh
python -m venv venv
```
- This creates a virtual environment named `venv` in the project directory.

#### 3. Activate the Virtual Environment
- **Windows:**
  ```sh
  venv\Scripts\activate
  ```
- **Linux/Mac:**
  ```sh
  source venv/bin/activate
  ```

#### 4. Install Dependencies
If your project has dependencies listed in `requirements.txt`, install them using:
```sh
pip install -r requirements.txt
```

#### 5. Running the Python Script
Once the virtual environment is activated, run your script:
```sh
python script.py  # Replace 'script.py' with the actual script name
```

#### 6. Deactivating the Virtual Environment
After finishing your work, deactivate the virtual environment using:
```sh
deactivate
```

### Additional Notes
- Always activate the virtual environment before running the script.
- If you add new dependencies, update `requirements.txt` using:
  ```sh
  pip freeze > requirements.txt
  ```
- To remove the virtual environment, delete the `venv` folder:
  ```sh
  rm -rf venv  # Linux/Mac
  rmdir /s /q venv  # Windows
  ```

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

