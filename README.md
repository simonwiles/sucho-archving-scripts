# sucho-archving-scripts

Scratch (mostly domain-specific?) scripts supporting SUCHO archiving efforts.

`elar.uspu.ru` includes a DSpace site with an OAI endpoint.  The script at <https://github.com/Segerberg/SUCHO/tree/master/DSpace_OAI-PMH> didn't output the URLs for the PDF files (not sure if it's supposed to?), so the script here scrapes those from the HTML for the records, to create a `seedFile` for passing to `browsertrix-crawler`.
