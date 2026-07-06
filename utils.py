import sys
import os

def get_asset_path(filename):
    """
    Resolve o caminho de um arquivo estático (imagem, etc) dependendo
    se o programa está rodando em ambiente dev ou dentro do PyInstaller.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)
