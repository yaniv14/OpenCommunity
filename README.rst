========================
Installing OpenCommunity
========================

OpenCommunity is an open source project from `Hasadna`_. Its aim is to help communities thrive in the Cloud.
Our first step is to support setting the agenda sork for the managment committee.
Join the conversation in our `google group`_ (English and Hebrew).

.. _Hasadna: http://www.hasadna.org.il
.. _google group: https://groups.google.com/forum/#!forum/omiflaga

Prerequisites for Developer Machines
====================================

* git
* python 2.7 (Windows users can install from http://www.ninite.com/ )
* On ubuntu 13.04::

    # Pillow build requirements:
    sudo apt-get install python-dev libjpeg-dev libjpeg8 zlib1g-dev libfreetype6 libfreetype6-dev


(Quick) Setup
=============

* Fork the repo and clone it to your computer using git clone
* cd into the cloned project
* You will need virtualenv.  Either install it or download virtualenv.py
  from here: https://raw.github.com/pypa/virtualenv/master/virtualenv.py
* Now create a virtualenv.  Use either::

      virtualenv .

  Or::

    python virtualenv.py .

* Good! to activate the env use this on OSX or linux::

    source bin/activate

  On windows::

    scripts\activate

* Your prompt should start with `(OpenCommunity)`.
* On windows install some binary packages first::

    windows-setup.cmd

* Now install all other requirements (This can take some time)::

    pip install -r requirements.txt

* Create a local settings file from the example file.  On linux/OSX::

    cp src/ocd/local_settings.py.example src/ocd/local_settings.py

  On windows::

    copy src\ocd\local_settings.py.example src\ocd\local_settings.py

* Now create a directory for your sqlite db::

    mkdir db

* It's time to get closer to our code::

    cd src

* ... and create the database::

    python manage.py syncdb
    python manage.py migrate

  (When asked, create a user for the admin interface)

* To start the dev web server::

    python manage.py runserver

* Profit: http://localhost:8000/

Collaborating
=============

* Setup your git repo to get upstream changes::

    git remote add upstream git://github.com/hasadna/OpenCommunity.git
    git pull upstream master


* Now go and get them::

    git pull upstream master
    pip install -r requirements.txt
    python manage.py syncdb
    python manage.py migrate


Common Problems and Solutions
=============================
* If the following message appear when running `python manage.py`::

    Django - "no module named django.core.management"
    
  You probably have not activated your virtualenv, or did not
  install the requirements.
