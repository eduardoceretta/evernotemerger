FROM python:3

WORKDIR /usr/src/app
COPY . .

# Upgrade PIP
# RUN python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --upgrade pip

# # Download and setup evernote SDK
# COPY evernote-sdk-python-master evernote
# WORKDIR /usr/src/app/evernote
# RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r evernote_requirements.txt
# RUN python setup.py install

# # Get requirements
# WORKDIR /usr/src/app
# COPY requirements.txt ./
# RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r requirements.txt

# # Get application
# COPY test.py .

# Run
CMD [ "python", "./test.py" ]