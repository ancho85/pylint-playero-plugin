pylint-playero-plugin
==========================

# About

`pylint-playero-plugin` is a [Pylint](http://pylint.org) plugin for improving code analysis for when analysing code using [Playero ERP](http://www.hbs.com.py).

## Usage

#### Pylint

Ensure `pylint-playero-plugin` is installed and on your path, and then run pylint:

```
pylint --load-plugins Playero [..other options..]
```

# Features

* Prevents warnings and errors about Playero-generated attributes, classes, methods. (Now fully supported)
* Xml record file parsing to get attributes of a table/class.
* Py file parsing to get methods, functions and attributes of a class.
* Inheritance is generated based on Playero's xml settings file.
* built-in methods, functions and attributes accepted.  (Now fully supported)
* SuperClass generation.
* NewRecord, NewReport, NewWindow generation.
* TODO: Query parsing and checking for syntax (milestone v0.3.0)

# License

`pylint-playero-plugin` is available under the GPLv2 license.
