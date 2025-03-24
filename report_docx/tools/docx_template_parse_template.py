from typing import Optional, Set
from docxtpl import DocxTemplate
from jinja2 import Environment
from jinja2.nodes import Name, Getattr


class DocxTemplateParseTemplate(DocxTemplate):  # расширяем класс для получения полных полей шаблона

    def get_all_template_variables(self, jinja_env: Optional[Environment] = None) -> Set[str]:
        self.init_docx(reload=False)
        xml = self.get_xml()
        xml = self.patch_xml(xml)
        for uri in [self.HEADER_URI, self.FOOTER_URI]:
            for relKey, part in self.get_headers_footers(uri):
                _xml = self.get_part_xml(part)
                xml += self.patch_xml(_xml)
        if jinja_env:
            env = jinja_env
        else:
            env = Environment()
        parse_content = env.parse(xml)

        variables = set()
        variables_internal = set()
        for name in parse_content.find_all(Name):
            if name.ctx == 'load':
                variables.add(name.name)
            else:
                variables_internal.add(name.name)

        def recurse_getattr(g: Getattr):
            if isinstance(g.node, Getattr):
                return recurse_getattr(g.node) + "." + g.attr
            return g.node.name + "." + g.attr

        for a in parse_content.find_all(Getattr):
            variables.add(recurse_getattr(a))

        fields = set()
        for v in variables:
            for f in v.split('.'):
                if f not in variables_internal:
                    fields.add(f)

        return fields
