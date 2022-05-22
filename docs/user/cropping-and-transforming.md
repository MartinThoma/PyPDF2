# Cropping and Transforming PDFs

```python
from PyPDF2 import PdfFileWriter, PdfFileReader

reader = PdfFileReader("example.pdf")
writer = PdfFileWriter()

# add page 1 from reader to output document, unchanged:
writer.addPage(reader.pages[0])

# add page 2 from reader, but rotated clockwise 90 degrees:
writer.addPage(reader.pages[1].rotateClockwise(90))

# add page 3 from reader, but crop it to half size:
page3 = reader.pages[2]
page3.mediaBox.upperRight = (
    page3.mediaBox.getUpperRight_x() / 2,
    page3.mediaBox.getUpperRight_y() / 2,
)
writer.addPage(page3)

# add some Javascript to launch the print window on opening this PDF.
# the password dialog may prevent the print dialog from being shown,
# comment the the encription lines, if that's the case, to try this out:
writer.addJS("this.print({bUI:true,bSilent:false,bShrinkToFit:true});")

# write to document-output.pdf
with open("PyPDF2-output.pdf", "wb") as fp:
    writer.write(fp)
```

## Plain Merge

![](plain-merge.png)

is the result of

```python
from PyPDF2 import PdfFileReader, PdfFileWriter, Transformation

# Get the data
reader_base = PdfFileReader("labeled-edges-center-image.pdf")
page_base = reader_base.pages[0]

reader = PdfFileReader("box.pdf")
page_box = reader.pages[0]

page_base.mergePage(page_box)

# Write the result back
writer = PdfFileWriter()
writer.addPage(page_base)
with open("merged-foo.pdf", "wb") as fp:
    writer.write(fp)
```

## Merge with Rotation

![](merge-45-deg-rot.png)

```python
from PyPDF2 import PdfFileReader, PdfFileWriter, Transformation

# Get the data
reader_base = PdfFileReader("labeled-edges-center-image.pdf")
page_base = reader_base.pages[0]

reader = PdfFileReader("box.pdf")
page_box = reader.pages[0]

# Apply the transformation
transformation = Transformation().rotate(45)
page_box.add_transformation(transformation)
page_base.mergePage(page_box)

# Write the result back
writer = PdfFileWriter()
writer.addPage(page_base)
with open("merged-foo.pdf", "wb") as fp:
    writer.write(fp)
```

If you add the expand parameter:

```python
transformation = Transformation().rotate(45)
page_box.add_transformation(transformation)
page_base.mergePage(page_box)
```

you get:

![](merge-rotate-expand.png)

Alternatively, you can move the merged image a bit to the right by using

```python
op = Transformation().rotate(45).translate(tx=50)
```

![](merge-translated.png)
