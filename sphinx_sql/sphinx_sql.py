from . import __version__
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict
import re
import json
from operator import itemgetter

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
    closing_regex = '((?=return:)|(?=purpose:)|(?=dependent objects:)|(?=changelog:)|(?=parameters)|(?=\*/))'
    regex_dict = {
        # Full comment block
        'top_sql_block_comments': '(?s)/\*.*?\*/',
        # Match Group 2 for Object Type, Group 3 for Object Name
        #'object': '^(create\s*or\s*replace\s*|create\s*|create\s*external\s*)(\w*)\s*((\w*)\.(\w*)|(\w*))',
        'object': '(?<=create)(.*?)((\w*)\.(\w*))',
        # Match Group 2 for distribution key, comma seperated for multiple keys
        'distributed_by': 'distributed by \(.*?\)',
        # Match Group 2 for partition type (range) Group 3 for parition key.
        'partition_by': 'partition by \(.*?\)',
        # Match Group 1 for language
        'language': '(language .*?)\;',
        'comments': {
            'object_name': '(?<=Object Name:)(\s\S*)',
            'object_type': '(?<=Object Type:)(\s\S*)',
            #'parameters': '(?s)(?<=parameters:)(.*?)(?=return:)',
            #'return_type': 'Return:(.?\w.*)',
            #'purpose': '(?s)(?<=purpose:)(.*?)((?=dependent objects:)|(?=\*/))',
            #'dependancies': '(?s)(?<=objects:)(.*?)(?=changelog:)',
            #changelog': '(?s)(?<=changelog:)(.*?)(?=\*)',
            'parameters': f'(?s)(?<=parameters:)(.*?){closing_regex}',
            'return_type': 'Return:(.?\w.*)',
            'purpose': f'(?s)(?<=purpose:)(.*?){closing_regex}',
            'dependancies': f'(?s)(?<=objects:)(.*?){closing_regex}',
            'changelog': f'(?s)(?<=changelog:)(.*?){closing_regex}',
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
    objname = re.compile(regex_strings.comments.object_name, re.IGNORECASE | re.MULTILINE)
    objtype = re.compile(regex_strings.comments.object_type, re.IGNORECASE | re.MULTILINE)
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
            logger.info(file)
            contents = f.read()
            object_details = {}
            if self.obj.findall(contents):
                # DDL file
                sql_type = self.obj.findall(contents)[0]

                if not sql_type[1]:
                    logger.warning(
                        "No top level comments found in file. Not a DML file. Skipping {}".format(file))
                    return None
                else:

                    # Read name and type from ANSI92 SQL objects first
                    object_details['type'] = str(sql_type[0]).upper().replace('OR REPLACE','').strip()
                    object_details['name'] = str(sql_type[1]).lower().strip()

                    if object_details['type'] == 'TABLE':
                        dist = self.objdist.findall(contents)
                        part = self.objpart.findall(contents)
                        object_details['distribution_key'] = dist
                        object_details['partition_key'] = part
                    elif object_details['type'] == 'FUNCTION':
                        lang = self.objlang.findall(contents)
                        object_details['language'] = lang

                    if self.top_comments.findall(contents):
                        comment = self.top_comments.findall(contents)[0]
                        object_details['comments'] = self.extract_comments(comment)
                    else:
                        object_details['comments'] = None
            else:
                # Likely a DML file
                dml = self.top_comments.findall(contents)[0]
                if dml:
                    oname = self.objname.search(str(dml))
                    otype = self.objtype.search(str(dml))
                    if not oname or not otype:
                        return None
                    else:
                        object_details['type'] = otype[0].rstrip('\\n').strip().upper()
                        object_details['name'] = oname[0].rstrip('\\n').strip().lower()
                        object_details['comments'] = self.extract_comments(str(dml))
                else:
                    return None
        object_details = json.loads(json.dumps(object_details), object_hook=lambda item: SimpleNamespace(**item))
        return object_details

    def extract_comments(self, str_comment):
        obj_comment = {}
        if self.objpara.findall(str_comment):
            #sparam = str(self.objpara.findall(str_comment)[0].strip('[]')).splitlines()
            sparam = self.objpara.findall(str_comment)[0]
            obj_comment['param'] = self.split_to_list(sparam)
        if self.objreturn.findall(str_comment):
            obj_comment['return_type'] = str(
                self.objreturn.findall(str_comment)[0]).lower().strip()
        if self.objpurpose.findall(str_comment):
            obj_comment['purpose'] = str(
                self.objpurpose.findall(str_comment)[0][0]).strip()
        if self.objdepen.findall(str_comment):
            #sod = str(self.objdepen.findall(str_comment)[0].strip('[]')).splitlines()
            sod = self.objdepen.findall(str_comment)[0]
            obj_comment['dependancies'] = self.split_to_list(sod)
        if self.objchange.findall(str_comment):
            #scl = str(self.objchange.findall(str_comment)[0].strip('[]')).splitlines()
            scl = self.objchange.findall(str_comment)[0]
            obj_comment['changelog'] = self.split_to_list(scl)

        return obj_comment

    def split_to_list(self, source):
        slist = []
        source = ''.join(source)
        source = [ x.strip() for x in source.splitlines() ]
        for line in self.non_blank_lines(source):
            sline = [ x.strip() for x in line.split('|') ]
            slist.append(sline)
        return slist

    def non_blank_lines(self, f):
        for l in f:
            line = l.rstrip()
            if line:
                yield line

    def convert_string_to_markup(self, s):
        ns = str(s).replace('\t', '    ')
        return ns

    def build_table(self, tabledata, is_dependant=False):
        table = n.table()
        tgroup = n.tgroup()
        tbody = n.tbody()

        for _ in range(len(tabledata[0])):
            colspec = n.colspec(colwidth=1)
            tgroup += colspec

        for tidx, row in enumerate(tabledata):
            r = n.row()
            for cidx, cell in enumerate(row):
                entry = n.entry()
                if is_dependant and tidx > 0 and cidx==1:
                    para = n.paragraph()
                    entry += para
                    para += n.reference(cell, cell, refuri='#{}'.format(n.make_id(cell)))
                else:
                    entry += n.Text(cell)

                r += entry
            tbody += r
        tgroup += tbody
        table += tgroup
        return table

    def build_table_row(self, rowdata):
        row = n.row()
        for cell in rowdata:
            entry = n.entry()
            row.append(entry)
            entry.append(cell)
        return row

    def extract_purpose(self, comments):
            # Purpose block
            lb = n.literal_block()
            purpose = self.convert_string_to_markup(comments.purpose)
            t = n.Text(purpose, purpose)
            lb += t
            return lb

    def build_docutil_node(self, core_text):
        section = n.section(ids=[n.make_id(core_text.name)])
        section += n.title(core_text.name, core_text.name)
        section += n.line("OBJECT TYPE: {}".format(core_text.type),
                          "OBJECT TYPE: {}".format(core_text.type))

        if core_text.type == 'FUNCTION':
            section += n.line("RETURNS: {}".format(core_text.comments.return_type),
                              "RETURNS: {}".format(core_text.comments.return_type))

            if hasattr(core_text, 'language') and len(core_text.language) > 0:
                section += n.line(core_text.language[0],core_text.language[0])

            # Parameters block
            section += n.line("","")
            section += n.line("PARAMETERS:","PARAMETERS:")
            if len(core_text.comments.param) > 1:
                ptable = self.build_table(core_text.comments.param)
                section += ptable
            else:
                section += n.line("None","None")
                section += n.line("","")

        if core_text.type == "TABLE":
            if hasattr(core_text, 'distribution_key') and len(core_text.distribution_key) > 0:
                section += n.line(core_text.distribution_key[0],core_text.distribution_key[0])
            if hasattr(core_text, 'partition_key') and len(core_text.partition_key) >0:
                section += n.line(core_text.partition_key[0],core_text.partition_key[0])

        if hasattr(core_text.comments, 'purpose'):
            # Purpose block
            section += n.line("","")
            section += n.line("PURPOSE:", "PURPOSE:")
            lb = self.extract_purpose(core_text.comments)
            section += lb

        if hasattr(core_text.comments, 'dependancies'):
            section += n.line("DEPENDANT OBJECTS:", "DEPENDANT OBJECTS:")
            dtable = self.build_table(core_text.comments.dependancies, True)
            section += dtable

        if hasattr(core_text.comments, 'changelog'):
            section += n.line("CHANGE LOG:", "CHANGE LOG:")
            ctable = self.build_table(core_text.comments.changelog)
            section += ctable

        return section

    def run(self):
        sections = []
        doc_cores = []
        sql_argument = self.options['sqlsource']
        srcdir = self.get_sql_dir(sqlsrc=sql_argument)
        sql_files = self.get_sql_files(srcpath=srcdir)

        # Extract doc strings from source files
        for file in sql_files:
            logger.debug("File: {}".format(file))
            core = self.extract_core_text(file)

            if not core:
                logger.warning("Did not find usable sphinx-sql comments in file: {}".format(file))
            else:
                doc_cores.append(core)

        # Sort docs into SQL object type and alphabetic object name
        sorted_cores = sorted(doc_cores, key=lambda x: (x.type,x.name))

        # Extract docutil nodes into lists of SQL object type
        section_types = defaultdict(list)
        for core in sorted_cores:
            section = self.build_docutil_node(core)
            section_types[core.type].append(section)
        # Create high level object type node and append child nodes from above
        for stype in section_types:
            top_section = n.section(ids=[n.make_id(stype)])
            top_section += n.title(stype, stype)

            for section in section_types[stype]:
                top_section += section

            # Append to master node list for return
            sections.append(top_section)
        return sections

def setup(app):
    app.add_directive("autosql", SqlDirective)
    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
