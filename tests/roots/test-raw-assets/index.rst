Raw assets
==========

Inline SVG block:

.. raw:: html

   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" xml:space="preserve"><rect width="10" height="10" fill="red"/></svg>

Inline base64 PNG inside img tag:

.. raw:: html

   <img alt="dot" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" />

Plain custom div should stay inline:

.. raw:: html

   <div class="custom-marker">just text</div>
