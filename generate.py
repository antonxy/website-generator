#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import re
import sys
import os
import shutil
import argparse

root_path = os.path.join(sys.path[0], '..')
sys.path.insert(1, root_path)
import config

languages = config.languages

def readInfoFile(path):
    d = {}
    reg = re.compile(r'^(.*)=(.*)$')
    with open(path, 'r', encoding='utf-8') as infof:
        for line in infof.readlines():
           res = reg.match(line)
           if res is not None:
               d[res.groups()[0]] = res.groups()[1]
    return d


class Structure(object):
    def __init__(self):
        self.root_page = Page()
        def recurse(path, page):
            page.path = path
            page.readFromInfo(readInfoFile(os.path.join(path, 'info')))
            for x in os.listdir(path):
                newPath = os.path.join(path, x)
                if os.path.isdir(newPath):
                    newPage = Page()
                    page.addChild(newPage)
                    recurse(newPath, newPage)
            page.sortChildren()
        recurse(os.path.join(root_path, 'content/pages/'), self.root_page)

    def getPageByUrl(self, url, lang):
        page = self.root_page
        while len(url) > 0:
            url_part = url[0]
            url = url[1:]
            foundPage = False
            for i in page.children:
                if i.urlPart(lang) == url_part:
                    page = i
                    foundPage = True
                    break
            if not foundPage:
                return None
        return page

    def getPageByPath(self, path_arr):
        page = self.root_page
        while len(path_arr) > 0:
            path_part = path_arr[0]
            path_arr = path_arr[1:]
            foundPage = False
            for i in page.children:
                if i.pathPart() == path_part:
                    page = i
                    foundPage = True
                    break
            if not foundPage:
                return None
        return page

    def printMenu(self, lang, filed, current_page=None):
        def visible_policy(page):
            if not page.visible():
                return False

            # Page is child of active
            if page.parent == current_page:
                return True

            # Page is active or indirect parent of active
            current_parent = current_page
            while current_parent is not None:
                if current_parent == page:
                    return True
                current_parent = current_parent.parent

            # Parent of page is indirect parent of active <=> Page is sibling of "active"
            current_parent = current_page
            while current_parent is not None:
                if current_parent == page.parent:
                    return True
                current_parent = current_parent.parent

            return False

        def recurse(page, depth, doRecursion=True):
            if page == current_page:
                print('<li class="active">', file=filed)
            else:
                print("<li>", file=filed)
            page.printLink(filed, lang)
            if doRecursion:
                visible_children = [x for x in page.children if visible_policy(x)]
                if len(visible_children) > 0:
                    print("<ul>", file=filed)
                    for item in visible_children:
                        recurse(item, depth + 1)
                    print("</ul>", file=filed)
            print("</li>", file=filed)
        print('<ul class="menu">', file=filed)
        # Show children of root page on level 0
        recurse(self.root_page, 0, False)
        root_visible_children = [x for x in self.root_page.children if visible_policy(x)]
        for p in root_visible_children:
            recurse(p, 0, True)
        print("</ul>", file=filed)


class Page(object):
    def __init__(self):
        self.parent = None
        self.children = []
        self.info = {}
        self.path = None

    def visible(self):
        return not 'invisible' in self.info or not self.info['invisible']

    def readFromInfo(self, info):
        self.info = info

    def addChild(self, child):
        self.children.append(child)
        child.parent = self

    def sortChildren(self):
        def getKey(child):
            return child.pathPartNum()
        self.children = sorted(self.children, key=getKey)

    def title(self, lang):
        return self.info['title-' + lang]

    def menuTitle(self, lang):
        if 'menutitle-' + lang in self.info:
            return self.info['menutitle-' + lang]
        else:
            return self.info['title-' + lang]

    def urlPart(self, lang):
        return self.info['url-' + lang]

    def pathPart(self):
        splitName = os.path.basename(self.path).split('+', maxsplit=1)
        return splitName[1] if len(splitName) >= 2 else splitName[0]

    def pathPartNum(self):
        splitName = os.path.basename(self.path).split('+', maxsplit=1)
        return int(splitName[0]) if len(splitName) >= 2 else 9999999

    def _url_no_lang(self, lang):
        url = ''
        if self.parent is not None:
            url += self.parent._url_no_lang(lang)
            url += '/'
        url += self.urlPart(lang)
        return url

    def url(self, lang):
        return '/' + lang + self._url_no_lang(lang) + '.html'

    def printLink(self, filed, lang, text=None):
        if text is None:
            text = self.menuTitle(lang)
        print('<a href="' + self.url(lang) + '">' + text + '</a>', file=filed)

    def printContent(self, lang, filed):
        template_regex = re.compile(r'{{([^}]*)}}')
        with open(os.path.join(self.path, lang+'.html'), 'r', encoding='utf-8') as content_file:
            for line in content_file.readlines():
                line_matches = template_regex.finditer(line)
                last_end = 0
                for line_match in line_matches:
                    values = line_match.groups()[0].split("|")
                    key = values[0]
                    params = values[1:]
                    filed.write(line[last_end:line_match.start()])
                    if key == 'href':
                        href_page = structure.getPageByPath(params)
                        if href_page is None:
                            print("In page ", self.path, " - language: ", lang, file=sys.stderr)
                            print("Could not find page with path: ", params, file=sys.stderr)
                        else:
                            filed.write(href_page.url(lang))
                    else:
                        filed.write('Undefined')
                    last_end = line_match.end()
                filed.write(line[last_end:len(line)])

    def printLanguages(self, filed):
        global languages
        print("<ul>", file=filed)
        for k, v in languages:
            print('<li>', file=filed)
            linkContent = '<img src="/images/languages/' + k + '.gif" title="' + v + '" alt="' + v + '"/>'
            self.printLink(filed, k, linkContent)
            print('</li>', file=filed)
        print("</ul>", file=filed)


def generatePage(structure, page, lang, root_dir, url = None):
    filename = root_dir + (page.url(lang) if url is None else url)
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    template_regex = re.compile(r'{{(.*)}}')

    with open(filename , 'w', encoding='utf-8') as filed:
        with open(os.path.join(root_path, 'template'), 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line_match = template_regex.search(line)
                if line_match is not None:
                    key = line_match.groups()[0]
                    filed.write(line[0:line_match.start()])
                    if key == 'content':
                        page.printContent(lang, filed)
                    elif key == 'menu':
                        structure.printMenu(lang, filed, page)
                    elif key == 'languages':
                        page.printLanguages(filed)
                    elif key == 'title':
                        print(page.title(lang), file=filed, end="")
                    elif key == 'language-code':
                        print(lang, file=filed, end="")
                    else:
                        filed.write('Undefined')
                    filed.write(line[line_match.end():len(line)])
                else:
                    filed.write(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", help="Directory the generated pages will be put into")
    args = parser.parse_args()
    structure = Structure()
    out_dir = args.out_dir if args.out_dir else '/var/www/html'

    #Delete existing output
    if os.path.exists(out_dir):
        for the_file in os.listdir(out_dir):
            file_path = os.path.join(out_dir, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)

    #Generate pages
    def recurse_pages(page):
        for lang, langname in languages:
            generatePage(structure, page, lang, out_dir)
        for c in page.children:
            recurse_pages(c)

    recurse_pages(structure.root_page)
    #Index with default language
    generatePage(structure, structure.root_page, config.default_language, out_dir, url='/index.html')

    #Copy static content
    src = os.path.join(root_path, 'content/static')
    src_files = os.listdir(src)
    for file_name in src_files:
        full_file_name = os.path.join(src, file_name)
        full_dest_name = os.path.join(out_dir, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, out_dir)
        else:
            shutil.copytree(full_file_name, full_dest_name)
