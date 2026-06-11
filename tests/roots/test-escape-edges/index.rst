Edge cases for MDX/JSX/Markdown escaping
========================================

External link with special characters: `Search "X & Y" <https://example.com/?q=X%20%26%20Y>`_.

An image with quotes in alt text:

.. image:: dot.png
   :alt: A "dotted" line & arrow

A figure with HTML-ish caption:

.. figure:: dot.png
   :alt: Dot

   Caption with <angle> & "quoted" text.

.. tab-set::

   .. tab-item:: a > b "best"

      Tab body.

.. card:: A & B "the rest"

   Card body content.
