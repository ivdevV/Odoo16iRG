import os, glob, codecs
from odoo.modules.module import get_module_path
path = get_module_path("website_forum")
print(path)
for p in glob.glob(os.path.join(path, "**", "*.xml"), recursive=True):
    with codecs.open(p, "r", "utf-8") as f:
        if "view_forum_forum_form" in f.read():
            print("MATCH", p)
            break
