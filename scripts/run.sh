. .ve/bin/activate # load local python environment
export PYTHONPATH=.
echo Running Daemons...
sleep 1
echo Running Auth Server...
python authsvr/authsvr.py &
sleep 1
echo Running Api Server...
python apisvr/apisvr.py &
sleep 1
