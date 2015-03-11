pylint-playero-plugin
==========================
[![status](https://sourcegraph.com/api/repos/github.com/ancho85/pylint-playero-plugin/.badges/status.png)](https://sourcegraph.com/github.com/ancho85/pylint-playero-plugin)
[![Build Status](https://travis-ci.org/ancho85/pylint-playero-plugin.svg?branch=master)](https://travis-ci.org/ancho85/pylint-playero-plugin)
[![Coverage Status](https://coveralls.io/repos/ancho85/pylint-playero-plugin/badge.svg)](https://coveralls.io/r/ancho85/pylint-playero-plugin)

# About

`pylint-playero-plugin` is a [Pylint](http://pylint.org) plugin for improving code analysis for when analysing code using [Playero ERP](http://www.hbs.com.py).

## Usage

#### Pylint

Ensure `pylint-playero-plugin` is installed and on your path, and then run pylint:

```
pylint --load-plugins Playero [..other options..]
```
[Read the wiki for usage with SublimeText](https://github.com/ancho85/pylint-playero-plugin/wiki/Configuration-with-SublimeText)

# Features

* Prevents warnings and errors about Playero-generated attributes, classes, methods. (Now fully supported)
* Xml record file parsing to get attributes of a table/class.
* Py file parsing to get methods, functions and attributes of a class.
* Inheritance is generated based on Playero's xml settings file.
* built-in methods, functions and attributes accepted.  (Now fully supported)
* SuperClass generation.
* NewRecord, NewReport, NewWindow generation.
* Query parsing and checking for syntax

# License

`pylint-playero-plugin` is available under the GPLv2 license.

# Required

* pylint-1.0.0

# Required to check mysql syntax:

* pyparsing-2.0.2
* MySQL-python-1.2.5
