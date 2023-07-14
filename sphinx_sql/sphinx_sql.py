from . import __version__
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict
import re
import json

from ddlparse import DdlParse

import docutils.nodes as n
from docutils.parsers.rst import Directive, directives

from sphinx.util import logging

logger = logging.getLogger(__name__)


class Config:
    """Sphinx sphinx-sql extension settings in `conf.py`.

    Attributes
    ---------
    sphinxsql_include_table_attributes : :obj:`bool` (Defaults to True)
        Extract Columns from Tables defined in DDL files.
    """

    _config_values = {
        "sphinxsql_include_table_attributes": (True, "env"),
    }

    def __init__(self, **settings):
        for name, (default, rebuild) in self._config_values.items():
            setattr(self, name, default)
        for name, value in settings.items():
            setattr(self, name, value)


# Define SQL Table types
TABLE_TYPES = ["TABLE", "EXTERNAL TABLE", "FOREIGN TABLE"]
# Define SQL object types consisting of two words
special_obj_type = [
    "EXTERNAL",
    "FOREIGN",
    "MATERIALIZED",
]


class SqlDirective(Directive):
    has_content = False
    option_spec = {"sqlsource": directives.unchanged}

    # Most of these regex strings should be case-insensitive lookups
    closing_regex = (
        r"((?=return:)|(?=purpose:)|(?=dependent objects:)|"
        r"(?=changelog:)|(?=parameters)|(?=\*/))"
    )
    regex_dict = {
        # Full comment block
        "top_sql_block_comments": r"(?s)/*.*?\*/",
        # Match Group 1 for Object Type, Group 3 for Object Name
        # in cluster and catalog objects (e.g. database, role; extension,
        #  schema)
        "object_cluster_catalog": r"(?<=create)\s+(\w+)\s*(if not exists)*\s"
        r'?("?[^\s*;]*"?)\s*',
        # Match Group 2 (a defined special object type, e.g. "materialized")
        # and Group 3 for Object Type, Group 5 for Object Name
        # in schema objects (e.g. table, view, function)
        "object_schema": rf"(?:(?<=create)|(?<=alter))\s*(or replace|or alter)?\s*("
        rf"{'|'.join(special_obj_type)}"
        rf")?\s*(\w+)\s*(if not exists)*\s?((\w*)\.(\"?[^\s*\(]*\"?))",
        # Match Group 2 for distribution key, comma separated for multiple keys
        "distributed_by": r"distributed by \(.*?\)",
        # Match Group 2 for partition type (range) Group 3 for partition key.
        "partition_by": r"partition by \(.*?\)",
        # Match Group 1 for language
        "language": r"(language .*?)\;",
        "comments": {
            "object_name": r"(?<=Object Name:)(\s\S*)",
            "object_type": r"(?<=Object Type:)(\s\S*)",
            "parameters": rf"(?s)(?<=parameters:)(.*?){closing_regex}",
            "return_type": r"Return:(.?\w.*)",
            "purpose": rf"(?s)(?<=purpose:)(.*?){closing_regex}",
            "dependencies": rf"(?s)(?<=objects:)(.*?){closing_regex}",
            "changelog": rf"(?s)(?<=changelog:)(.*?){closing_regex}",
        },
        # Match Group 1 for Schema, Group 2 for Table Name,
        # Group 3 for Field Name, Group 4 for Comment on Column
        "col_comment": r"(?<=comment on column)\s*(\w*)\.(\w*)"
        r"\.(\w*)\s*IS.*'(.*)';",
        # Match complete Constraint part
        "constraints": r"^\s*CONSTRAINT.*\n*.*\),?",
        # Match create table definition and everything below
        # (strip out anything above ie: pg_dump statements)
        "table_definition": r"(create .*)",
    }

    regex_strings = json.loads(
        json.dumps(regex_dict), object_hook=lambda item: SimpleNamespace(**item)
    )

    # Compile Top Level Regex
    obj_cluster_catalog = re.compile(
        regex_strings.object_cluster_catalog, re.IGNORECASE | re.MULTILINE
    )
    obj_schema = re.compile(regex_strings.object_schema, re.IGNORECASE | re.MULTILINE)
    objdist = re.compile(regex_strings.distributed_by, re.IGNORECASE | re.MULTILINE)
    objpart = re.compile(regex_strings.partition_by, re.IGNORECASE | re.MULTILINE)
    objlang = re.compile(regex_strings.language, re.IGNORECASE | re.MULTILINE)
    top_comments = re.compile(
        regex_strings.top_sql_block_comments, re.IGNORECASE | re.MULTILINE
    )

    # Compile Comment Regex
    objname = re.compile(
        regex_strings.comments.object_name, re.IGNORECASE | re.MULTILINE
    )
    objtype = re.compile(
        regex_strings.comments.object_type, re.IGNORECASE | re.MULTILINE
    )
    objpara = re.compile(
        regex_strings.comments.parameters, re.IGNORECASE | re.MULTILINE
    )
    objreturn = re.compile(
        regex_strings.comments.return_type, re.IGNORECASE | re.MULTILINE
    )
    objpurpose = re.compile(
        regex_strings.comments.purpose, re.IGNORECASE | re.MULTILINE
    )
    objdepen = re.compile(
        regex_strings.comments.dependencies, re.IGNORECASE | re.MULTILINE
    )
    objchange = re.compile(
        regex_strings.comments.changelog, re.IGNORECASE | re.MULTILINE
    )

    # Complie SQL Comment on Column Regex
    objcol_comment = re.compile(regex_strings.col_comment, re.IGNORECASE | re.MULTILINE)

    # Complie SQL Constraint Regex
    objconstraints = re.compile(regex_strings.constraints, re.IGNORECASE | re.MULTILINE)

    objtable = re.compile(
        regex_strings.table_definition, re.IGNORECASE | re.MULTILINE | re.DOTALL
    )

    def get_sql_dir(self, sqlsrc):
        env = Path(self.state.document.settings.env.srcdir)
        path = Path.resolve(Path.joinpath(env, sqlsrc))
        return path

    def get_sql_files(self, srcpath):
        files = Path(srcpath).rglob("*.sql")
        return files

    def extract_sql_col_comments(self, ddl, schema_name, table_name):
        """Return SQL Comment Statements on Columns.
        Helper function for extract_columns().
        """

        col_comments = self.objcol_comment.findall(ddl)
        table_column_comments = []
        for col_comment in col_comments:
            # Check Schema
            if col_comment[0] == schema_name:
                # Check Table
                if col_comment[1] == table_name:
                    table_column_comments.append(col_comment)

        return table_column_comments

    def extract_columns(self, contents, schema_name, table_name):
        """Extract Table Columns and their metadata
        from DDL code.
        """

        # Extract just create and everything below (removes pg_dump meta info)
        contents = self.objtable.search(contents).group()

        # Get DDL and clean content for ddlparse
        if len(self.top_comments.findall(contents)) > 0:
            # If Top Level Comment exists
            top_comments = self.top_comments.findall(contents)[0]

            # Remove Top Level Comment to parse plain DDL
            ddl = contents.replace(top_comments, "")

            if len(self.objconstraints.findall(ddl)) > 0:
                # Remove Constraints because Check Constraints
                # cannot be parsed properly by ddlparse
                constraints = self.objconstraints.findall(ddl)
                for constraint in constraints:
                    ddl = ddl.replace(constraint, "")
        elif len(self.objconstraints.findall(contents)) > 0:
            # If no Top Level Comment exists,
            # but Constraint Statements exist
            ddl = contents
            constraints = self.objconstraints.findall(ddl)

            # Remove Constraints because Check Constraints
            # cannot be parsed properly by ddlparse
            for constraint in constraints:
                ddl = ddl.replace(constraint, "")
        else:
            # No Top Level Comment, no Constraint Statements
            ddl = contents

        parser = DdlParse()
        parser.ddl = ddl
        table = parser.parse()

        table_column_comments = self.extract_sql_col_comments(
            ddl, schema_name, table_name
        )

        # Define header fields for sphinx-table
        fields = [["Name", "Type", "Description"]]

        for col in table.columns.values():
            # Extract column metadata
            if col.precision and col.scale:
                data_type = f"{col.data_type}({col.precision},{col.scale})"
            elif col.length:
                data_type = f"{col.data_type}({col.length})"
            else:
                data_type = col.data_type

            if len(table_column_comments) > 0:
                # Find SQL Comment on current Column
                for column_comment in table_column_comments:
                    if col.name == column_comment[2]:
                        comment = column_comment[3]
                        break
                    else:
                        comment = ""
            else:
                comment = ""

            # Build list of rows for sphinx-table
            field = [col.name.lower(), data_type.lower(), comment]
            fields.append(field)

        return fields

    def extract_core_text(self, config, file):
        with open(file) as f:
            logger.info(file)
            contents = f.read()
            object_details = {}
            if self.obj_schema.findall(contents):
                sql_type_schema = self.obj_schema.findall(contents)[0]
                sql_type = (
                    f"{sql_type_schema[1]} {sql_type_schema[2]}",
                    sql_type_schema[4],
                    sql_type_schema[5],
                    sql_type_schema[6],
                )
            elif self.obj_cluster_catalog.findall(contents):
                sql_type_cluster_catalog = self.obj_cluster_catalog.findall(contents)[0]
                # Create a tuple matching to length of obj_schema
                sql_type = (
                    sql_type_cluster_catalog[0],
                    sql_type_cluster_catalog[2],
                    "",
                    "",
                )
            try:
                if "sql_type" in locals():
                    # DDL file
                    # Read name and type from ANSI92 SQL objects first
                    object_details["type"] = str(sql_type[0]).upper().strip()
                    if object_details["type"] == "PROC":
                        object_details["type"] = "PROCEDURE"

                    object_details["name"] = (
                        str(sql_type[1]).lower().strip().replace('"', "")
                    )

                    if object_details["type"] in TABLE_TYPES:
                        dist = self.objdist.findall(contents)
                        part = self.objpart.findall(contents)
                        object_details["distribution_key"] = dist
                        object_details["partition_key"] = part
                        if config.sphinxsql_include_table_attributes:
                            try:
                                object_details["cols"] = self.extract_columns(
                                    contents, sql_type[2], sql_type[3]
                                )
                            except Exception:
                                # If no columns can be extracted
                                object_details["cols"] = []

                    elif object_details["type"] in {"FUNCTION", "PROCEDURE"}:
                        lang = self.objlang.findall(contents)
                        object_details["language"] = lang

                    if self.top_comments.findall(contents):
                        comment = self.top_comments.findall(contents)[0]
                        object_details["comments"] = self.extract_comments(comment)
                    else:
                        object_details["comments"] = None
                else:
                    # Likely a DML file
                    dml = self.top_comments.findall(contents)[0]
                    if dml:
                        oname = self.objname.search(str(dml))
                        otype = self.objtype.search(str(dml))
                        if not oname or not otype:
                            return None
                        else:
                            object_details["type"] = (
                                otype[0].rstrip("\\n").strip().upper()
                            )
                            object_details["name"] = (
                                oname[0].rstrip("\\n").strip().lower()
                            )
                            object_details["comments"] = self.extract_comments(str(dml))
                    else:
                        return None
            except Exception as e:
                logger.warning(
                    f"""No top level comments found in file.
                    The exception raised: {e}.
                    Not a DML file. Skipping {file}"""
                )
                return None

        object_details = json.loads(
            json.dumps(object_details), object_hook=lambda item: SimpleNamespace(**item)
        )

        return object_details

    def extract_comments(self, str_comment):
        obj_comment = {}
        if self.objpara.findall(str_comment):
            sparam = self.objpara.findall(str_comment)[0]
            obj_comment["param"] = self.split_to_list(sparam)
        if self.objreturn.findall(str_comment):
            obj_comment["return_type"] = (
                str(self.objreturn.findall(str_comment)[0]).lower().strip()
            )
        if self.objpurpose.findall(str_comment):
            obj_comment["purpose"] = str(
                self.objpurpose.findall(str_comment)[0][0]
            ).strip()
        if self.objdepen.findall(str_comment):
            sod = self.objdepen.findall(str_comment)[0]
            obj_comment["dependencies"] = self.split_to_list(sod)
        if self.objchange.findall(str_comment):
            scl = self.objchange.findall(str_comment)[0]
            obj_comment["changelog"] = self.split_to_list(scl)

        return obj_comment

    def split_to_list(self, source):
        slist = []
        source = "".join(source)
        source = [x.strip() for x in source.splitlines()]
        for line in self.non_blank_lines(source):
            sline = [x.strip() for x in line.split("|")]
            slist.append(sline)
        return slist

    def non_blank_lines(self, f):
        for vline in f:
            line = vline.rstrip()
            if line:
                yield line

    def convert_string_to_markup(self, s):
        ns = str(s).replace("\t", "    ")
        return ns

    def build_table(self, titles: str, tabledata: str, is_dependant: bool = False):
        table = n.table()
        tgroup = n.tgroup()
        tbody = n.tbody()

        for _ in range(len(tabledata[0])):
            colspec = n.colspec(colwidth=1)
            tgroup += colspec

        for tidx, row in enumerate(tabledata):
            header = n.row()
            for title in titles:
                header += n.entry("", n.paragraph(text=title))
            r = n.row()
            for cidx, cell in enumerate(row):
                entry = n.entry()
                if is_dependant and tidx >= 0 and cidx == 1:
                    para = n.paragraph()
                    entry += para
                    para += n.reference(
                        cell, cell, refuri="#{}".format(n.make_id(cell))
                    )
                else:
                    entry += n.Text(cell)

                r += entry
            tbody += r
        tgroup += n.thead("", header)
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
        lb["language"] = "none"
        purpose = self.convert_string_to_markup(comments.purpose)
        t = n.Text(purpose, purpose)
        lb += t
        return lb

    def build_docutil_node(self, core_text):
        section = n.section(ids=[n.make_id(core_text.name)])
        section += n.title(core_text.name, core_text.name)
        section += n.line(
            "OBJECT TYPE: {}".format(core_text.type),
            "OBJECT TYPE: {}".format(core_text.type),
        )

        if core_text.type in {"FUNCTION", "PROCEDURE"}:
            if core_text.type == "FUNCTION":
                section += n.line(
                    "RETURNS: {}".format(core_text.comments.return_type),
                    "RETURNS: {}".format(core_text.comments.return_type),
                )

            if hasattr(core_text, "language") and len(core_text.language) > 0:
                section += n.line(core_text.language[0], core_text.language[0])

            # Parameters block
            section += n.line("", "")
            section += n.line("PARAMETERS:", "PARAMETERS:")
            # The first row is treated as table header
            if len(core_text.comments.param) > 1:
                ptable = ""
                try:
                    ptable = self.build_table(
                        core_text.comments.param[0],  # table header
                        core_text.comments.param[1:],  # data rows
                    )
                    section += ptable
                except Exception as e:
                    logger.warning(
                        f"""Unable to parse function parameters from {core_text.name}.
                        The exception raised: {e}.
                        Check your .sql source comments for proper
                        formatting!"""
                    )
            else:
                section += n.line("None", "None")
                section += n.line("", "")

        if core_text.type in TABLE_TYPES:
            if (
                hasattr(core_text, "distribution_key")
                and len(core_text.distribution_key) > 0
            ):
                section += n.line(
                    core_text.distribution_key[0], core_text.distribution_key[0]
                )
            if hasattr(core_text, "partition_key") and len(core_text.partition_key) > 0:
                section += n.line(
                    core_text.partition_key[0], core_text.partition_key[0]
                )

        if hasattr(core_text.comments, "purpose"):
            # Purpose block
            section += n.line("", "")
            section += n.line("PURPOSE:", "PURPOSE:")
            lb = self.extract_purpose(core_text.comments)
            section += lb

        if hasattr(core_text.comments, "dependencies"):
            # len over 1 means we've found dependant object rows past the
            # header; otherwise ignore the dependencies section even if its
            # included in the comments
            if len(core_text.comments.dependencies) > 1:
                section += n.line("DEPENDANT OBJECTS:", "DEPENDANT OBJECTS:")
                # The first row is treated as table header
                dtable = ""
                try:
                    dtable = self.build_table(
                        core_text.comments.dependencies[0],  # table header
                        core_text.comments.dependencies[1:],  # data rows
                        True,
                    )
                except Exception as e:
                    logger.warning(
                        f"""Unable to parse dependant objects from {core_text.name}.
                         The exception raised: {e}.
                         Check your .sql source comments for proper
                         formatting!"""
                    )
                section += dtable

        if core_text.type in TABLE_TYPES:
            if hasattr(core_text, "cols") and len(core_text.cols) > 0:
                # Attributes block
                section += n.line("ATTRIBUTES:", "ATTRIBUTES:")
                atable = ""
                # The first row is treated as table header
                try:
                    atable = self.build_table(
                        core_text.cols[0],  # table header
                        core_text.cols[1:],  # data rows
                    )
                except Exception as e:
                    logger.warning(
                        f"""Unable to parse table attributes
                        from {core_text.name}. The exception raised: {e}.
                        Check your .sql source comments for proper
                        formatting!"""
                    )
                section += atable

        if hasattr(core_text.comments, "changelog"):
            section += n.line("CHANGE LOG:", "CHANGE LOG:")
            # The first row is treated as table header
            ctable = ""
            try:
                ctable = self.build_table(
                    core_text.comments.changelog[0],  # table header
                    core_text.comments.changelog[1:],  # data rows
                )
            except Exception as e:
                logger.warning(
                    f"""Unable to parse change log from {core_text.name}.
                    The exception raised: {e}. Check your .sql source
                    comments for proper formatting!"""
                )
            section += ctable

        return section

    def run(self):
        # Read configuration variables from BuildEnvironment
        env = self.state.document.settings.env
        config = env.config

        sections = []
        doc_cores = []
        sql_argument = self.options["sqlsource"]
        srcdir = self.get_sql_dir(sqlsrc=sql_argument)
        sql_files = self.get_sql_files(srcpath=srcdir)

        # Extract doc strings from source files
        for file in sql_files:
            logger.debug("File: {}".format(file))
            core = self.extract_core_text(config, file)

            if not core:
                logger.warning(
                    f"Did not find usable sphinx-sql comments in file: {file}"
                )
            else:
                doc_cores.append(core)

        # Sort docs into SQL object type and alphabetic object name
        sorted_cores = sorted(doc_cores, key=lambda x: (x.type, x.name))

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
    for name, (default, rebuild) in Config._config_values.items():
        app.add_config_value(name, default, rebuild)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
