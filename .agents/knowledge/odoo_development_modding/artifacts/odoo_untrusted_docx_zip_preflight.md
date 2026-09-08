# Preflight de ZIP/DOCX no confiable antes de `ZipFile`

## Decisión reutilizable

Cuando un endpoint Odoo admite DOCX aportados por usuarios, no se debe llamar primero a `ZipFile.infolist()`. Antes de que la librería materialice un `ZipInfo` por cada entrada controlada por el archivo, se inspeccionan los bytes crudos del EOCD y del directorio central con límites estrictos.

El preflight debe:

- localizar un EOCD completo dentro de la ventana permitida por el formato;
- rechazar ZIP64 y archivos multidisco;
- limitar el tamaño del directorio central y el número declarado de entradas;
- recorrer y contar realmente todas las cabeceras del directorio central;
- exigir que el conteo real coincida con el declarado;
- comprobar offsets, límites y correspondencia de nombre entre cabecera central y local;
- rechazar datos comprimidos que invadan el directorio central.

Solo después se abre el archivo con `ZipFile`. En esa segunda fase se vuelven a limitar entradas, tamaño total descomprimido, ratio de compresión y tamaño leído por miembro. Para DOCX también se comprueba la presencia única de `[Content_Types].xml` y `word/document.xml`, sus content types/namespaces y se rechaza XML con DTD o entidades.

## Motivo

Los contadores del EOCD son metadatos no confiables: pueden falsificarse para eludir un límite previo. Abrir el ZIP antes de validar el directorio central permite que un archivo pequeño provoque una asignación masiva de objetos o trabajo desproporcionado. Comparar el conteo declarado con el recorrido real cierra esa discrepancia antes de entrar en la API de alto nivel.

## Aplicabilidad

Este patrón aplica a portales, importadores, controladores HTTP, asistentes y APIs que procesen ZIP, DOCX, XLSX, PPTX u otros formatos contenedores suministrados por usuarios. No sustituye el límite de bytes crudos ni las validaciones semánticas específicas del formato.
