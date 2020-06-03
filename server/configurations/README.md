#How to run on a mini-codac machine with psps installed (single user version of hieratika)

#Download hieratika
git clone https://github.com/aneto0/hieratika.git

#Change to the psps branch
git hieratika
git checkout -b develop-psps origin/develop-psps

#Install all the requirements
su
cd server
pip install -r requirements.txt
exit

#Start the server
python2.7 -m hieratika.wservermain -H 0.0.0.0 -p 7000 -i ../demo/server/psps/psps.standalone.ini
#Or (preferred)
gunicorn --preload -k gevent -w 8 -b 0.0.0.0:7000 'hieratika.wservermain:start(config="../demo/server/psps/psps.standalone.ini")'

#Open either chrome or opera and point at
http://127.0.0.1:7000
