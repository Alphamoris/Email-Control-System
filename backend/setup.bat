@echo off
echo Creating Python virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo Setting up pre-commit hooks...
pre-commit install

echo Setup complete! Run 'venv\Scripts\activate' to activate the virtual environment.
