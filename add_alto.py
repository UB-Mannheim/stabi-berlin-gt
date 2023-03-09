#!/usr/bin/python3

# Add new fileGrp sections for THUMBS and FULLTEXT to existing mets file.

# The script reads the existing METS file `mets`.
# It writes the result to a new METS file `fulltext-mets.xml`.

import re
import sys
import xml.dom.minidom

BASE_URL = 'https://ub-backup.bib.uni-mannheim.de/~stweil/gt/stabi-berlin'

# Extract from METS file:
#
# [...]
#   <mets:fileGrp USE="DEFAULT">
#     <mets:file ID="FILE_0001_DEFAULT" MIMETYPE="image/jpg">
#       <mets:FLocat xmlns:xlink="http://www.w3.org/1999/xlink" LOCTYPE="URL" xlink:href="https://content.staatsbibliothek-berlin.de/dc/PPN813172837-00000001/full/max/0/default.jpg"/>
#     </mets:file>
# [...]
# <mets:structMap TYPE="PHYSICAL">
#   <mets:div CONTENTIDS="http://resolver.staatsbibliothek-berlin.de/SBB00018A0E00010000" ID="PHYS_0000" TYPE="physSequence">
#     <mets:div CONTENTIDS="http://resolver.staatsbibliothek-berlin.de/SBB00018A0E00010001" ID="PHYS_0001" ORDER="1" ORDERLABEL=" - " TYPE="page">
#       <mets:fptr FILEID="FILE_0001_PRESENTATION"/>
#       <mets:fptr FILEID="FILE_0001_DEFAULT"/>
#       <mets:fptr FILEID="FILE_0001_THUMBS"/>
#     </mets:div>
# [...]

# https://docs.python.org/3/library/xml.dom.html
p = xml.dom.minidom.parse('mets')
metsPrefix = ''
fileSecs = p.getElementsByTagName('fileSec')
if len(fileSecs) == 0:
    metsPrefix = 'mets:'
    fileSecs = p.getElementsByTagName(metsPrefix + 'fileSec')
fileSec = fileSecs[0]

fileGrps = p.getElementsByTagName(metsPrefix + 'fileGrp')

fileGrpDefault = None
fileGrpFulltext = None
fileGrpThumbs = None
for fg in fileGrps:
    if fg.getAttribute('USE') == 'DEFAULT':
        fileGrpDefault = fg
    if fg.getAttribute('USE') == 'FULLTEXT':
        fileGrpFulltext = fg
    if fg.getAttribute('USE') == 'THUMBS':
        fileGrpThumbs = fg

if not fileGrpDefault:
    print('Missing fileGrp DEFAULT')
elif fileGrpFulltext:
    print('Existing fileGrp FULLTEXT')
else:
    print('Missing fileGrp FULLTEXT')
    fptrs = p.getElementsByTagName(metsPrefix + 'fptr')
    # Add fileGrp FULLTEXT.
    fileGrp = p.createElement(metsPrefix + 'fileGrp')
    fileGrp.setAttribute('USE', 'FULLTEXT')
    #for fileDefault in fileGrpDefault.childNodes:
    for fileDefault in fileGrpDefault.getElementsByTagName(metsPrefix + 'file'):
        id = fileDefault.getAttribute('ID')
        altoID = re.sub(r'DEFAULT$', r'FULLTEXT', id)
        thumbID = re.sub(r'DEFAULT$', r'THUMBS', id)
        for fptr in fptrs:
            if fptr.getAttribute('FILEID') == id:
                fptrAlto = p.createElement(metsPrefix + 'fptr')
                fptrAlto.setAttribute('FILEID', altoID)
                fptr.parentNode.appendChild(fptrAlto)
                if not fileGrpThumbs:
                    fptrThumb = p.createElement(metsPrefix + 'fptr')
                    fptrThumb.setAttribute('FILEID', thumbID)
                    fptr.parentNode.appendChild(fptrThumb)
                break
        flocat = fileDefault.getElementsByTagName(metsPrefix + 'FLocat')[0]
        href = flocat.getAttribute('xlink:href')
        # href="https://content.staatsbibliothek-berlin.de/dc/PPN813172837-00000627/..."
        match = re.match(r'^http.*(PPN[^/-]+)-([0-9]+)/.*', href)
        ppn = match.group(1)
        name = match.group(2)
        xlink = flocat.getAttribute('xmlns:xlink')
        file = p.createElement(metsPrefix + 'file')
        file.setAttribute('xmlns:xlink', xlink)
        file.setAttribute('ID', altoID)
        file.setAttribute('MIMETYPE', 'text/xml')
        FLocat = p.createElement(metsPrefix + 'FLocat')
        FLocat.setAttribute('LOCTYPE', 'URL')
        FLocat.setAttribute('xlink:href', BASE_URL + '/' + ppn + '/alto/' +  name + '.xml')
        file.appendChild(FLocat)
        fileGrp.appendChild(file)
        fileSec.appendChild(fileGrp)
    if not fileGrpThumbs:
        # Add fileGrp THUMBS.
        fileGrp = p.createElement(metsPrefix + 'fileGrp')
        fileGrp.setAttribute('USE', 'THUMBS')
        for fileDefault in fileGrpDefault.childNodes:
            id = fileDefault.getAttribute('ID')
            thumbID = re.sub(r'^file', r'thmb', id)
            flocat = fileDefault.getElementsByTagName(metsPrefix + 'FLocat')[0]
            href = flocat.getAttribute('xlink:href')
            href = re.sub(r'full/full', r'full/,150', href)
            file = p.createElement(metsPrefix + 'file')
            file.setAttribute('ID', thumbID)
            file.setAttribute('MIMETYPE', 'image/jpeg')
            FLocat = p.createElement(metsPrefix + 'FLocat')
            FLocat.setAttribute('LOCTYPE', 'URL')
            FLocat.setAttribute('xlink:href', href)
            file.appendChild(FLocat)
            fileGrp.appendChild(file)
            fileSec.appendChild(fileGrp)

out = open('fulltext-mets.xml', 'w')
for line in p.toprettyxml(indent='  ').split('\n'):
    line = line.rstrip()
    if line == '':
        continue
    print(line, file=out)
