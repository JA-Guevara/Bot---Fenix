# domain/login_interface.py

from abc import ABC, abstractmethod

class LoginStrategy(ABC):
    @abstractmethod
    async def login(self, page):
        pass

    @abstractmethod
    async def pre_download(self, page):
        pass

    @abstractmethod
    async def descargar_reportes(self, page):
        pass

    @abstractmethod
    async def logout(self, page):
        pass

