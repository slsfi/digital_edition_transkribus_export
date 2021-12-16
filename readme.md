# About

The TEI Transkribus Exporter will export TXT and facsimiles for a project created on the Digital Edition platform.

## How to run tei-transcribus-exporter.py
------------------------------
You can run the script with the first and only argument being a path to a directory or xml-file. If you supply a path to a directory, then all xml files inside that 

directory that match a filename pattern will be processed. The script will create a new directory in the directory of the processed file(s) with all pages saved as text 

files with their facsimile files added. Examples:

*    python tei-transcribus-exporter.py 1_3_est.xml
*    python tei-transcribus-exporter.py "D:\Work\topelius_xml"

## Dependencies
------------------------------
This script depends on two libraries, lxml and psycopg2.
  
tei-transcribus-exporter.py
------------------------------
There are a number of constants you need to change according to your environment, these are:

*    FACSIMILES_PATH = "..."                     # Should point to the folder where facsimiles are stored
*    FACSIMILES_SIZE = 4                         # 1-4, 1=smallest, 4=largest
*    FILE_XSLT_STRIP = "tei_strip.xslt"          # The xslt file used to strip elements from the input xml files
*    FILE_PATTERN = "*_est.xml"                  # Filename pattern to use when looking for input files if a path is supplied as argument
*    DB_... =                                    # Database connection parameters
  
## tei-strip.xslt
------------------------------
This file removes unnessecary elements from the source xml files and creates an as compact version as possible for the SAX parser in the Python script. It can be edited 

to preserve tags for certain elements. By default, add and del are preserved.
