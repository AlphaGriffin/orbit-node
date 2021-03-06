################################################################
ORBIT Node - Validation for Op_Return Bitcoin-Implemented Tokens
################################################################

.. image:: https://badges.gitter.im/AlphaGriffin/orbit.svg
   :alt: Join the chat at https://gitter.im/AlphaGriffin/orbit
   :target: https://gitter.im/AlphaGriffin/orbit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

**A node for processing and validating tokens on Bitcoin Cash implementing the ORBIT standard.**

The official website for ORBIT is http://orbit.cash.

.. contents:: Table of Contents
   :depth: 2
   :local:


************
Introduction
************

An ORBIT Node is a program that processes ORBIT-related information found on the Bitcoin Cash blockchain. It works in conjuction with an existing BCH Node (such as the Bitcoin-ABC bitcoind program) to review transactions containing OP_RETURN data and determine if they are valid ORBIT transactions and compute current balances for ORBIT tokens. A small database is utilized to track the verified ORBIT events and maintain balance information. Through a socket RPC interface, the ORBIT Node may be queried to retrieve token balances and history.

ORBIT Node is open source and licensed under the MIT license. See the `LICENSE <LICENSE>`_ file for more details.


The ORBIT Ecosystem
===================

ORBIT is a specification for simple, fungible tokens implemented by utilizing OP_RETURN for the storage of token events on the Bitcoin Cash blockchain. No changes to the Bitcoin Cash protocol or nodes are required. However, wallets may wish to incorporate this token standard in order to allow the user to easily take account of and interact with tokens that adhere to this ORBIT standard.

The following projects, when used in conjunction with ORBIT Node, complete a full ecosystem for tokens on Bitcoin Cash using ORBIT:

- ORBIT Specification and API: https://github.com/AlphaGriffin/orbit
- ORBIT Command-Line Interface: https://github.com/AlphaGriffin/orbit-cli
- ORBIT Qt Wallet: https://github.com/AlphaGriffin/orbit-gui
- ORBIT Web: https://github.com/AlphaGriffin/orbit-web


*************
Specification
*************

The ORBIT repository at https://github.com/AlphaGriffin/orbit defines the official and complete specification for ORBIT. 

*The current specification version is: 0 (beta testing). Version 0 is reserved and should be used for all testing.*



************
Contributing
************

Your help is appreciated! Alpha Griffin is a small team focused on developing new technology projects. If you have questions or comments or would like to contribute to the ORBIT node or ecosystem in any way, please feel free to contact us. You may submit issues or pull requests directly on GitHub or communicate with the team members at the following locations:

- https://gitter.im/AlphaGriffin
- https://alphagriffintrade.slack.com

Have a suggestion or request? Let us know!


To-Do List
==========

There are a number of tasks already identified on the `To-Do list <TODO>`_ that could use your help (included here in generated documentation).

.. include:: TODO
   :literal:



**********
ORBIT Node
**********

This ORBIT Node is written in Python.

.. toctree::
   API Documentation <api/modules>


Dependencies
============

- Python 3
- ORBIT API: https://github.com/AlphaGriffin/orbit (``pip install git+https://github.com/AlphaGriffin/orbit``)
- appdirs: https://github.com/ActiveState/appdirs (``pip install appdirs``)
- BitCash >= 0.5.2.4: https://github.com/sporestack/bitcash (``pip install bitcash\>=0.5.2.4``)
- python-bitcoinrpc: https://github.com/jgarzik/python-bitcoinrpc (``pip install python-bitcoinrpc``)
- Flask (``pip install flask``)
- *For building documentation (optional):* sphinx and sphinx_rtd_theme (``pip install sphinx sphinx_rtd_theme``)


In addition to the above, ORBIT Node requires RPC access to a local or remote Bitcoin Cash Node such as the one provided by Bitcoin ABC (https://www.bitcoinabc.org).


Build Overview
==============

Both a Makefile and setup.py are provided and used. The setup.py uses Python's standard setuptools package and you can call this script directly to do the basic Python tasks such as creating a wheel, etc.

The most common project build tasks are all provided in the Makefile. To see the full list of project targets::

    make help

Sphinx is used to generate html documentation and man pages. All documentation (html as well as man pages) may be regenerated at any time with::

    make docs

Every so often, when new source class files are created or moved, you will want to regenerate the API documentation templates. These templates may be modified by hand so this task does not overwrite existing files; you'll need to remove any existing files from ``api/`` that you want recreated. Then generate the API templates and re-build all documentation as follows::

    make apidoc
    make docs

There's not much to do for a simple Python project but your build may want to do more. In any case you can call ``make python`` if you need to (in orbit this target simply delegates to ``./setup.py build``).

Build all the common tasks (including documentation) as follows::

    make all

To clean up all the common generated files from your project folder::

    make clean


Installing
==========

To install this project to the local system::

    make install

Note that you may need superuser permissions to perform the above step.


Using
=====

**FIXME**



*******
History
*******

All changes are tracked in the `CHANGELOG <CHANGELOG>`_ file.

.. include:: CHANGELOG
   :literal:

----

*"Orbit the moon"*

