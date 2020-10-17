from . import __version__
from pathlib import Path
from types import SimpleNamespace
import re
import json

import docutils.nodes as n
from docutils.parsers.rst import Directive, directives

import sphinx
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.util import logging

logger = logging.getLogger(__name__)


class SqlDirective(Directive):

    has_content = False
    option_spec = {'sqlsource': directives.unchanged}

    # Most of these regex strings should be case insesitive lookups
    regex_dict = {
        # Full comment block
        'top_sql_block_comments': '(?s)/\*.*?\*/',
        # Match Group 2 for Object Type, Group 3 for Object Name
        'object': '^(create\s*or\s*replace\s*|create\s*)(\w*)\s*((\w*)\.(\w*)|(\w*))',
        # Match Group 2 for distribution key, comma seperated for multiple keys
        'distributed_by': 'distributed by \((.*)\)',
        # Match Group 2 for partition type (range) Group 3 for parition key.
        'partition_by': '(partition by )(\w*.)\((\w*)\)',
        # Match Group 1 for language
        'language': 'language (.*)\;',
        'comments': {
            'parameters': '(?s)(?<=parameters:)(.*?)(?=return:)',
            'return_type': 'Return:(.?\w.*)',
            'purpose': '(?s)(?<=purpose:)(.*?)(?=dependent objects:)',
            'dependancies': '(?s)(?<=depends:)(.*?)(?=changelog:)',
            'changelog': '(?s)(?<=changelog:)(.*?)(?=\*)',
        }
    }

    regex_strings = json.loads(json.dumps(
        regex_dict), object_hook=lambda item: SimpleNamespace(**item))

    # Compile Top Level Regex
    obj = re.compile(regex_strings.object, re.IGNORECASE | re.MULTILINE)
    objdist = re.compile(regex_strings.distributed_by,
                         re.IGNORECASE | re.MULTILINE)
    objpart = re.compile(regex_strings.partition_by,
                         re.IGNORECASE | re.MULTILINE)
    objlang = re.compile(regex_strings.language, re.IGNORECASE | re.MULTILINE)
    top_comments = re.compile(
        regex_strings.top_sql_block_comments, re.IGNORECASE | re.MULTILINE)

    # Complie Comment Regex
    #objname = re.compile(regex_strings.comments.name, re.IGNORECASE|re.MULTILINE)
    objpara = re.compile(regex_strings.comments.parameters,
                         re.IGNORECASE | re.MULTILINE)
    objreturn = re.compile(
        regex_strings.comments.return_type, re.IGNORECASE | re.MULTILINE)
    objpurpose = re.compile(regex_strings.comments.purpose,
                            re.IGNORECASE | re.MULTILINE)
    objdepen = re.compile(regex_strings.comments.dependancies,
                          re.IGNORECASE | re.MULTILINE)
    objchange = re.compile(regex_strings.comments.changelog,
                           re.IGNORECASE | re.MULTILINE)

    def get_sql_dir(self, sqlsrc):
        env = Path(self.state.document.settings.env.srcdir)
        path = Path.resolve(Path.joinpath(env, sqlsrc))
        return path

    def get_sql_files(self, srcpath):
        files = Path(srcpath).rglob('*.sql')
        return files

    def extract_core_text(self, file):
        with open(file) as f:
            contents = f.read()
            object_details = {}
            if self.obj.findall(contents):
                sql_type = self.obj.findall(contents)[0]

            if sql_type[1]:
                object_details['type'] = str(sql_type[1]).upper().strip()
                object_details['name'] = str(sql_type[2]).lower().strip()
                if object_details['type'] == 'TABLE':
                    dist = str(self.objdist.findall(contents)).strip('[]')
                    part = str(self.objpart.findall(contents)).strip('[]')
                    object_details['distribution_key'] = dist
                    object_details['partition_key'] = part
                elif object_details['type'] == 'FUNCTION':
                    lang = str(self.objlang.findall(contents)).strip('[]')
                    object_details['language'] = lang

                if self.top_comments.findall(contents):
                    comment = self.top_comments.findall(contents)[0]
                    object_details['comments'] = self.extract_comments(comment)
                else:
                    object_details['comments'] = None
                object_details = json.loads(json.dumps(
                    object_details), object_hook=lambda item: SimpleNamespace(**item))
                return object_details
            else:
                logger.warning(
                    "No object type found in file. Not a DML file. Skipping {}".format(file))
                return None

    def extract_comments(self, str_comment):
        obj_comment = {}
        if self.objpara.findall(str_comment):
            sparam = str(self.objpara.findall(str_comment)
                         [0].strip('[]')).splitlines()
            obj_comment['param'] = self.split_to_list(sparam)
        if self.objreturn.findall(str_comment):
            obj_comment['return'] = str(
                self.objreturn.findall(str_comment)[0]).lower().strip()
        if self.objpurpose.findall(str_comment):
            obj_comment['purpose'] = str(
                self.objpurpose.findall(str_comment)[0]).strip()
        if self.objdepen.findall(str_comment):
            obj_comment['dependancies'] = str(
                self.objdepen.findall(str_comment)).lower().strip()
        if self.objchange.findall(str_comment):
            scl = str(self.objchange.findall(str_comment)
                      [0].strip('[]')).splitlines()
            obj_comment['changelog'] = self.split_to_list(scl)

        return obj_comment

    def split_to_list(self, source):
        slist = []
        for line in self.non_blank_lines(source):
            sline = [x.strip() for x in line.split('|')]
            slist.append(sline)
        return slist

    def non_blank_lines(self, f):
        for l in f:
            line = l.rstrip()
            if line:
                yield line

    def build_docutil_node(self, core_text):
        section = n.section(ids=n.make_id(core_text.name))
        section += n.title(core_text.name, core_text.name)
        section += n.subtitle("Object Type: " + core_text.type, "Object Type: " + core_text.type)

        if core_text.type == 'FUNCTION':
            # fields = n.field_list()
            # field_name = n.field_name(text='Purpose')
            # field_body = n.field_body()
            # field_body.append(n.paragraph(str(core_text.comments.purpose).splitlines()))
            # field = n.field('', field_name, field_body)
            # fields += field
            # section += fields

            para = n.paragraph()
            purpose = (
                str(core_text.comments.purpose)
            )
            para = n.Text(purpose,purpose)

            section += para

        return section

    def run(self):
        sections = []
        sql_argument = self.options['sqlsource']
        srcdir = self.get_sql_dir(sqlsrc=sql_argument)
        sql_files = self.get_sql_files(srcpath=srcdir)
        for file in sql_files:
            logger.info("File: {}".format(file))
            core = self.extract_core_text(file)
            section = self.build_docutil_node(core)
            sections.append(section)
        return sections


def setup(app):
    app.add_directive("autosql", SqlDirective)
    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
