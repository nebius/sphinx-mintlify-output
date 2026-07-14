project = "Domains"
extensions = ["sphinx_mintlify_output"]
exclude_patterns = ["_build"]
master_doc = "index"


def setup(app):
    """Register a tiny domain with no entry in SIGNATURE_STYLES.

    Exercises the fallback path: bare signature in a ``text`` fence.
    """
    from typing import ClassVar

    from sphinx import addnodes
    from sphinx.directives import ObjectDescription
    from sphinx.domains import Domain

    class ThingDirective(ObjectDescription):
        def handle_signature(self, sig, signode):
            signode += addnodes.desc_name(sig, sig)
            return sig

    class AcmeDomain(Domain):
        name = "acme"
        label = "Acme"
        directives: ClassVar = {"thing": ThingDirective}

    app.add_domain(AcmeDomain)
