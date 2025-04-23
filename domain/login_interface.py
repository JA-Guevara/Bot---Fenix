# domain/login_interface.py

from abc import ABC, abstractmethod

class LoginStrategy(ABC):
    @abstractmethod
    async def login(self, page):
        """
        Método obligatorio para realizar login en un portal.
        """
        pass
