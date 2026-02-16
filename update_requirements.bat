@echo off
echo ===============================
echo Mise a jour requirements.txt
echo ===============================

call .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip freeze > requirements.txt

echo.
echo Le requirements.txt mis a jour
pause
