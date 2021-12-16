
# Imports
# ---------------------------------------------------------------
import sys, os, fnmatch, re, shutil
from shutil import copyfile
import psycopg2
import xml.sax
import lxml.etree as ET

# Constants (change according to your environment)
# ---------------------------------------------------------------
FACSIMILES_PATH = "facsimile" # Should point to the folder where facsimiles are stored
FACSIMILES_SIZE = 4 # 1-4, 1=smallest, 4=largest
FILE_XSLT_STRIP = "tei_strip.xslt" # The xslt file used to strip elements from the input xml files
FILE_PATTERN = "*.xml" # Filename pattern to use when looking for input files if a path is supplied as argument
EXPORT_PATH = "export" # Should point to the folder where facsimiles are stored
DB_HOST = ""
DB_DATABASE = ""
DB_USER = ""
DB_PASSWORD = ""

conn_new_db = psycopg2.connect(
    host=DB_HOST,
    database=DB_DATABASE,
    user=DB_USER,
    port="5432",
    password=DB_PASSWORD
)
c = conn_new_db.cursor()


# Custom content handler class used for the SAX XML Parser
# ---------------------------------------------------------------
class StreamHandler(xml.sax.handler.ContentHandler):

  pages = []
  pageContent = ""

  def startElement(self, name, attrs):
    # Add a linebreak if br-element reached
    if name == "br":
      self.pageContent += "\n"
    # Add current text content to the list of pages when a pb element is reached
    elif name == "pb":
      self.pages.append(self.pageContent)
      self.pageContent = ""
    # Add opening tag for all other elements except TEI (unwanted tags should be removed using tei-strip.xslt)
    elif name != "TEI":
      self.pageContent += "<"+name+">"

  def endElement(self, name):
    # Is the end of the TEI element reached?
    if name == "TEI":
      self.pages.append(self.pageContent)
    # Add closing tag for all other elements
    elif name != "pb" and name != "br":
      self.pageContent += "</"+name+">"

  def characters(self, content):
    # Add text node to page content
    self.pageContent += content

  def clearPages(self):
    # Clear pageContent and the pages list
    self.pageContent = ""
    self.pages.clear()

# Main program
# ---------------------------------------------------------------

# Check that a folder / file argument is supplied
if len(sys.argv) < 2:
  print("No input xml file / path provided!")
  sys.exit

else:
  argument_path = ""
  argument_filename = ""

  # Filename or folder name supplied as argument?
  if os.path.isfile("data/"+ sys.argv[1]):
    argument_filename = sys.argv[1]
  elif os.path.isdir(sys.argv[1]):
    argument_path = sys.argv[1]

  print(argument_path)
  # Create a list of files to process
  # ---------------------------------------------------------------
  
  # Create an empty list for input files
  input_files = [] #
  # If a folder name is supplied, find all files matching the pattern
  if len(argument_path)>0:
    for dirpath, dirnames, filenames in os.walk(argument_path):
      if not filenames:
        continue
      _files = fnmatch.filter(filenames, FILE_PATTERN)
      if _files:
        for file in _files:
          input_files.append(file)
  elif len(argument_filename)>0:
      input_files.append(argument_filename)

  # Process files if the list of files is not empty 
  # ---------------------------------------------------------------
  if len(input_files)>0:

    # Iterate the input file list
    for xml_input_filename in input_files:
    
      # Get the basename of the input xml file name
      file_output_basename = os.path.basename(xml_input_filename)
      file_output_basename = os.path.splitext(file_output_basename)[0]
      
      publication_id = file_output_basename.split('_')[1]

      # Set output folder to input file folder + filename (excl. extension)
      path_output = EXPORT_PATH + "/" +  os.path.splitext(xml_input_filename)[0]
      path_output2 = path_output + "/txt"
      
      # Create the output folder if it doesn't exist
      if not os.path.exists(path_output2):
        os.makedirs(path_output2)

      # Print info about file being processed
      print("--------------------------------------")
      print("Processing: "+xml_input_filename)
      print("Output folder: "+path_output2)


      # Open the xml file
      dom = ET.parse("data/"+xml_input_filename)
      # Get the item id from the header of the xml file
      ns = {"tei": "http://www.tei-c.org/ns/1.0"}
      itemId = dom.xpath("/tei:TEI/tei:teiHeader/tei:profileDesc/tei:creation/tei:idNo[not(@type='bookid')]", namespaces=ns)
      # Open the xslt file used for stripping tags from the input xml
      xslt = ET.parse(FILE_XSLT_STRIP)
      # Create a xslt transform object instance
      transform = ET.XSLT(xslt)
      # Transform the input xml using the provided xslt file
      newdom = transform(dom)
      
      # Convert the transformed xml to a utf-8 formatted string
      str_out = ET.tostring(newdom, pretty_print=False, encoding='UTF-8').decode('UTF-8')
      # Normalize all whitespace (multiple white space characters will become one space)
      str_out = re.sub( r'\s+', ' ', str_out ).strip()
      # Add xml declaration to the xml string
      str_out = '<?xml version="1.0" encoding="UTF-8" ?>\n' + str_out

      # Parse the transformed xml using a SAX parser and an instance of the custom StreamHandler class (above)
      # --------------------------------------------------------
      handler = StreamHandler()
      handler.clearPages()
      xml.sax.parseString(str_out, handler)

      # Save all extracted pages to separate text files
      for i in range(len(handler.pages)):
        text_file = open(os.path.join(path_output2, file_output_basename+"_"+str(i+1)+".txt"), "w", encoding='UTF-8')
        text_file.write(handler.pages[i].strip())
        text_file.close()

      # Print number of pages
      print("Page count: " + str(len(handler.pages)))

      # Get the facsimiles
      # --------------------------------------------------------

      # Get the correct row from the database (facsimiles, publications_facsimiles, publications)
      c.execute(""" SELECT pfc.id, pfc.start_page_number, pf.page_nr FROM publication_facsimile pf
                    JOIN publication_facsimile_collection pfc ON pf.publication_facsimile_collection_id = pfc.id 
                    WHERE pf.publication_id = %s
                """, (publication_id,) )
      # Get the row
      if c.rowcount > 0:
        print("Copying facsimiles...")
        # Get the first (and only row)
        res = c.fetchone()
        # Iterate all pages created when processing the file using the SAX parser
        for i in range(len(handler.pages)):
          # Create the path to the source facsimile file
          facs_src = os.path.join(FACSIMILES_PATH, str(res[0]), str(FACSIMILES_SIZE), str(res[1]+res[2]+i)+".jpg")
          # Create the path to the destination facsimile file
          facs_dest = os.path.join(path_output, file_output_basename+"_"+str(i+1)+".jpg")
          # If source facsimile file exists then copy it to destination
          if os.path.isfile(facs_src):
            copyfile( facs_src, facs_dest)
            print(facs_src + " --> " + facs_dest)
          else:
            print(facs_src + " not found!" )
      else:
        print("This file has no associated facsimiles!")
        shutil.rmtree(path_output)
  else:
    print("No files to process!")

print("--------------------------------------")