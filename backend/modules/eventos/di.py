from injector import Module, Binder

from modules.eventos.domain.selectors.evento_selector import EventoSelector


class EventosModule(Module):
    def configure(self, binder: Binder) -> None:
        """Register the selectors owned by the eventos module."""
        binder.bind(EventoSelector, to=EventoSelector)
