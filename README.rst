esmlib
------

**esmlib** is a poorly-designed library for reading data from Gamebryo ESM/ESP files. It does not include any provision for interpreting record data beyond that required to read past them to the next record, and any non trivial application will require heavy lifting on your part. It only supports Oblivion and possibly Morrowind ESMs, though SKyrim/FO4 suport should be doable. It is written for Python 3.6, but will likely work on earlier 3.x releases. It requires no other libraries.

Here's a usage example

::

 esm = esmlib.openESM('Oblivion.esm')
 esm.interestingTopGroups = [b'LTEX']
 esm.load()

This loads only the Land TEXture group, and will complete very quickly. After this, you can access the groups in ``esm.groups``, each of which contains ``group.contents``, as well as ``.subgroups`` and ``.records``, which are filtered versions of ``.contents``. Records and groups also contain metadata that is vital to understanding what they contain. For groups, this is ``.groupType`` and ``.label``. For records, this is ``.type``, ``.flags``, and ``.formid``, as well as the ``.subrecords`` generator, which should really be an interator but isn't. Subrecords have ``type``, ``dataSize``, and ``data``. There's some other stuff that you might need for some reason; check the source for the Group and Record types in ``esmlib.py``.

Shitty documentation about what data is where is available at the Unofficial Elder Scrolls Pages: http://en.uesp.net/wiki/Tes4Mod:Mod_File_Format

By default, esmlib will read all groups except for CELL and WRLD, the interior and exterior worldspaces, which will require about 80 MB of memory for Oblivion.esm. Loading the CELL group will require about 340 MB of memory, while the WRLD group will require 1.2 GB.

An ugly example script that uses esmlib to extract the heightmap data for Cyrodiil is available in ``extract heightmap.py``. It requires Pillow and patience.


Alternatives
------------
`Wrye Bash`_ is written in Python 2, and has actual support for interpreting lots of record and group types. I don't know if using their libraries is easy though.

bethesdalib_ seems to target TES5 and has Py2-3 support, but seems abandoned, and the 'source archive' has Cython-generated C code, so good luck interpreting or modifying it. The email there is for 'gandaganza', and there's a user of that name on Skyrim Nexus and Twitter. Maybe bug them for source?

pyESP_ is a tool for writing ESP files.

.. _`Wrye Bash`: https://github.com/wrye-bash/wrye-bash
.. _bethesdalib: https://pypi.org/project/bethesdalib/2.0a2/
.. _pyESP: https://github.com/palmettos/pyESP