
import pandas as pd

def exportar_excel(productos):
    df = pd.DataFrame(productos)
    path = 'productos.xlsx'
    df.to_excel(path, index=False)
    return path
