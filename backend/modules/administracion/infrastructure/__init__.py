"""
Infrastructure layer of the administracion module.

The administrative surface is READ-ONLY and consumes the selectors of the
business modules, so this layer has no concrete adapter yet: the concrete
implementations live in the OWNING modules (that is where the data and its
rules are).
"""
