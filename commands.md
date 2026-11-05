
git clone YOUR_REPOSITORY_URL

cd T103-PS-057

python -m venv venv

venv\Scripts\activate

python3 -m venv venv
source venv/bin/activate

python -m pip install -r requirements.txt

python main.py

python -m unittest discover -s tests -v


## After making changes

git status
git add .
git commit -m "Describe your changes"
git push





## Important Notes

- Run commands from the project root directory.
- Activate the virtual environment before installing or running dependencies.
- Do not upload virtual environment folders to GitHub.
- Do not modify shared input data without coordinating with teammates.
- Pull the latest changes before starting new work.
- Commit and push completed changes regularly.