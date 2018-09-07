# Índice de Sentimiento de Reportes de Estabilidad Financiera

## Objetivo
Cálculo del *ISREF* para los Reportes de Estabilidad Financiera, producidos por el Banco de la República de Colombia, que han sido traducidos a inglés.

## Antecedentes

Investigadores de  la FED publicaron en 2017 un Discussion Paper llamado
[Sentiment in Central Bank's Financial Stability Reports](https://www.federalreserve.gov/econres/ifdp/files/ifdp1203.pdf), en el que construyen un índice que mide el sentimiento expresado en el texto de los Reportes de Estabilidad Financiera publicados por diferentes bancos centrales en el período 2005 - 2015.

El *FSS index* se calcula, para cada reporte, como la diferencia entre la cantidad de palabras negativas y positivas, relativo a la cantidad total de palabras que lo componen.

*FSS = (#negativas - #positivas)/#total*.

 Para esto construyeron un [diccionario de palabras positivas y negativas](https://www.federalreserve.gov/econres/ifdp/files/ifdp1203-appendix.xlsx), considerando que el uso de las palabras tiene una connotación diferente, en el contexto de sentimiento de comunicaciones de estabilidad financiera, si se compara con su uso común y con otros diccionarios generales y financieros.

 ### Nota
No se busca replicar el Paper. Solo el proceso de cálculo aplicado a los informes del BanRep.

## Contenido
- extraction.py
    - Se usa para extraer el texto de archivos pdf y word usando TIKA.
    - Crea una carpeta *corpus* en el directorio donde están los documentos originales, almacenando el texto de cada documento en un archivo txt.
    - Crea, si no existe, *procesados.csv* donde se incluye metadata de cada documento al que se le realize extracción. Si ya existe se actualiza con nuevas filas.

    **Modo de uso**:

    python extraction.py <path/to/original/docs/>

- helpers.py
    - Contiene funciones, variables y clases comunes que pueden ser usadas en diferentes archivos.
    - Otros archivos la llaman con

        *import helpers as hp*

- notebooks exploratorios
