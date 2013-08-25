Deployment Instructions
=======================

* On a new Ubuntu 13.04 Server, run as root::

    # Create an oc user
    adduser oc
    # ... and specify a password.

    # update your system
    apt-get update
    apt-get upgrade

    # install some packages
    apt-get install postgresql nginx supervisor python virtualenvwrapper git python-dev libpq-dev libjpeg-dev libjpeg8 zlib1g-dev libfreetype6 libfreetype6-dev

    # Create postgres user
    sudo -iu postgres createuser oc -S -D -R

    # create postgres db and grant permisions
    sudo -iu postgres createdb opencommunity -O oc

For best luck, uncomment the following line in `/etc/nginx/nginx.conf`::

    server_names_hash_bucket_size 64;


Le'ts install a send-only mail server as well::

    apt-get install postfix
    # select Internet Site and your domain
    # make sure that myhostname = opencommunity.org.il here:
    vi /etc/postfix/main.cf
    # and reload your server
    /etc/init.d/postfix reload

    # test your mail server:
    sendmail youremail@gmail.com
    # enter some text
    # hit Ctrl+D
    # it's probably in your spam folder, don't panic.


Now log in as `oc` either via ssh or by running `su - oc` and execute::

    # clone the repo to your home dir...
    git clone https://github.com/hasadna/OpenCommunity.git

    # ...go inside...
    cd OpenCommunity

    # create a virtualenv 
    mkvirtualenv oc
    # your prompt should now start with (oc)

    # install the requirements
    pip install -r requirements.txt
    pip install -r deploy-requirements.txt

    # create a local settings file
    cp src/ocd/local_settings.py.example src/ocd/local_settings.py

    # now edit it:
    vi src/ocd/local_settings.py

It should look like this::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2', 
            'NAME': 'opencommunity',
        }
    }
    _host = 'www.opencommunity.org.il'
    HOST_URL = "http://%s" % _host
    ALLOWED_HOSTS = [_host]
    FROM_EMAIL = "noreply@opencommunity.org.il"

Let's set up the database::

    cd src
    python manage.py syncdb
    python manage.py migrate

    # Create a superuser to allow yourself an access to the admin
    python manage.py createsuperuser

    # And while we are here:
    python manage.py collectstatic --noinput

Let's set up a gunicorn server, back as root::

    mkdir /var/log/opencommunity/

    cp /home/oc/OpenCommunity/conf/nginx.conf /etc/nginx/sites-available/opencommunity
    ln -s /etc/nginx/sites-available/opencommunity /etc/nginx/sites-enabled/opencommunity

    cp /home/oc/OpenCommunity/conf/supervisor.conf /etc/supervisor/conf.d/opencommunity.conf

    # restart services
    service nginx start
    service supervisor stop
    service supervisor start

Now go to <http://opencommunity.org.il/>