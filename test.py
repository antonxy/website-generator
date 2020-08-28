from jinja2 import Environment, FileSystemLoader
import http.server
import socketserver
import tempfile
import os
import shutil
from PIL import Image
from resizeimage import resizeimage

env = Environment(loader=FileSystemLoader(['templates']))

loader=FileSystemLoader(['content/pages'])

args = {
    "title": "Testpage",
    "language_code": "de"
}

pages = [
    "/de.html",
    "/10+membrane/de.html"
]

PORT = 5000
with tempfile.TemporaryDirectory() as out_dir:
    print(out_dir)

    src = 'content/static'
    src_files = os.listdir(src)
    for file_name in src_files:
        full_file_name = os.path.join(src, file_name)
        full_dest_name = os.path.join(out_dir, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, out_dir)
        else:
            shutil.copytree(full_file_name, full_dest_name)

    def generate_image(path, width):
        print(f"generate_image {path} {width}")
        new_name = os.path.splitext(path)[0] + "-" + str(width) + os.path.splitext(path)[1]
        with open(out_dir + path, 'r+b') as f:
            with Image.open(f) as image:
                img = resizeimage.resize_width(image, width)
                img.save(out_dir + new_name, image.format)
        return new_name

    env.globals['image'] = generate_image


    def generate_page(path):
        print(f"generate_page {path}")
        template = loader.load(env, path)

        filename = out_dir + path

        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(filename, "w") as fh:
            fh.write(template.render(**args))

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=out_dir, **kwargs)

        def send_head(self):
            print(self.path)
            if self.path in pages:
                generate_page(self.path)
            return super().send_head()


    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
