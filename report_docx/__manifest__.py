{
    "name": "Base report docx",
    "summary": "Base module to create docx report",
    "author": "",
    "website": "",
    "category": "Reporting",
    "version": "16.0.0.0",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["docx", "docxtpl"]},
    "depends": ["base", "web"],
    "installable": True,
    "assets": {
        "web.assets_backend": [
            "report_docx/static/src/js/report/action_manager.js"
        ],
    },
    "data": [
        'views/ir_report.xml'
    ],
}
