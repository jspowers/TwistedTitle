# """
# RUN THIS SCRIPT TO SETUP THE ENVIRONMENT FOR THE PROJECT
# $ source setup_env.sh
# """

# Step 1: Create virtual environment
python3 -m venv venv

# Step 2: Activate virtual environment
source venv/bin/activate

# Step 3: Install dependencies from requirements.txt
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found"
    exit
fi

# Step 4: Export current working directory to the PythonPath variable
export PYTHONPATH="$(pwd)"
echo "PYTHONPATH is set to: $PYTHONPATH"

echo "Setup complete. Virtual environment created and dependencies installed."