Tables with special characters
==============================

GFM table with pipes
--------------------

.. list-table::
   :header-rows: 1

   * - Symbol
     - Meaning
   * - ``a | b``
     - logical or
   * - ``c & d``
     - logical and
   * - ``e < f``
     - less than

GFM table with HTML-ish text
----------------------------

.. list-table::
   :header-rows: 1

   * - Tag
     - Note
   * - tag <strong>
     - keep literal
   * - amp & co
     - ampersand

Complex table with special chars
--------------------------------

+-----+-------------+
| Col | Val         |
+=====+=============+
| A   | x | y       |
+-----+-------------+
| B   | a & b < c   |
+-----+-------------+
| C   | one         |
|     | two         |
+-----+-------------+
