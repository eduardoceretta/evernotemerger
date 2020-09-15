# Meta

Based on Evernote for Sublime Text plugin


# Local

docker-machine.exe restart box
eval $("docker-machine" env box)

source env.secrets

_ssh_agent_create
ssh-add ../../AppData/GitHubSsh/id_rsa
(fraca num)

docker build -t python-test -f docker/Dockerfile .

docker run --rm --name my-running-app -e EVERNOTE_DEV_TOKEN -e EVERNOTE_DEV_NOTESTORE_URL -v "/Projetos/EvernoteMerger:/usr/src/app" python-test


# Heroku
Setup
  heroku buildpacks:set heroku/python
  heroku config:set EVERNOTE_DEV_TOKEN=XXXXXXXXXXXXXXXX
  heroku config:set EVERNOTE_DEV_NOTESTORE_URL=XXXXXXXXXXXXXXXX

Cron
  Setup
     heroku addons:create scheduler:standard
  Test
    heroku run python bin/merger.py
  Schedule
    heroku addons:open scheduler

Deployment:
  heroku login
  cat $HOME/_netrc
  git push heroku master
    username (from cat $HOME/_netrc)
    password (from cat $HOME/_netrc)