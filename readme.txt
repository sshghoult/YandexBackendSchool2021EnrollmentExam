Deployment instructions:

1. install docker and docker-compose on your server
2. git clone the repository
3. via vim or another text editor change passwords in cfg.py and docker-compose files (those to be changed are marked as PLACEHOLDERs) (note that mysql virtual interface`s port is bound to the actual port of the machine, you can turn it off by deleting "ports:" part in the definition of the service. stated is also a reason for you to choose secure passwords for the DB, if the latest 20 years of the internet's history haven't taught you to)
4. run docker-compose with appropriate arguments (see the official documentation) (the application service will fall a couple of times before the DB service will be initialised, it's a docker-related bug to be fixed later)
5. port 8080, if you haven't changed it, is ready to accept requests
