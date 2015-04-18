# ikez (beta)

ikez is a tool to ease use setup of buildout based Odoo appservers.

Typically the following command will build a complete running Odoo 8 even on a freshly installed Ubuntu 12.04 or 14.04.

```bash
ikez odoo install -u admv8 -r http://github.com/cmorisse/appserver-templatev8 -d appserver-v8
```

ikez is just an automation (running on MacOS and Ubuntu) of the steps described there: http://docs.anybox.fr/anybox.recipe.odoo/1.9.1/first_steps.html#how-to-create-and-bootstrap-a-buildout

ikez is written in pure python and is distributed as a single executable file that installs nothing in your system python.
See packaging section below for detail.

##Version
ikez is in its infancy (use --version) but it used on a daily basis.

Version 1.0 will mark the end of the beta period.

##Installation

Get the ikez executable and copy it to a directory on your system $PATH.
```sh
wget https://raw.githubusercontent.com/cmorisse/ikez/master/release/ikez
```

###From source

Clone this repository, "cd" into it, then launch:

```sh
./instlocal.sh
./setup_local_cache.sh
./makeit.sh
```
Finally copy the built **release/ikez** in a directory on your system path.
 
##Usage

ikez main command is "odoo install".

Use -h to get all options:

```bash
ikez -h
ikez odoo -h
ikez odoo install -h
```

Other commands, are sub commands of odoo install.

### Warning
To run an odoo install, ikez must be used with an ikez compatible repository.

Technically (and today) they are repository with:

- a buildout.cfg.template file
- a project_addons directoty

http://github.com/cmorisse/appserver-templatev8 is a ready to use ikez compatible repository.

### Interesting options

With --training, ikez will print each command before executing it.

## Supported platforms

ikez supports:

- Ubuntu 14.04
- Ubuntu 12.04
- Mac OSX 10.10
- Debian 7
- Debian 8

Redhat Linux flavor support would be welcome.

## Licence

ikez is GPL 3.0 Licensed.


## Roadmap

- Implement --json
- Implement a settings module
- Deactivate color when ouput is redirected
- Rework architecture to ease per system / distrib / version customizations


## Packaging

ikez is written in Python, completely self contained ; it installs nothing on your system beyond the ikez executable.

Technically it is zip file that has been set executable.

This packaging is done by the **makeit.sh** script.
 
### References

How to create a zip from a set of python files and packages:

- http://stackoverflow.com/questions/17486578/how-can-you-bundle-all-your-python-code-into-a-single-zip-file

How to make the zip executable:

- http://blog.ablepear.com/2012/10/bundling-python-files-into-stand-alone.html

## Beyond Odoo

ikez is not restricted to Odoo. 
In the future, ikez will ease the setup of others applications build with buildout (eg. Django).

#Note for the users of appserver-templatev7 or muppy

ikez will replace install.sh and it will be used extensively by muppy v3.
