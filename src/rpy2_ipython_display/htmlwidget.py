"""
Taken from https://github.com/rpy2/rpy2/issues/646
and https://github.com/rpy2/rpy2-ipython-display
to allow plotly in rpy2 magic
"""
from pathlib import Path
from IPython.display import HTML, display
from rpy2.robjects.packages import importr

base = importr('base')
htmlwidgets  = importr('htmlwidgets')

def htmlwidget(interactive_plot, args):
    knitr_output = htmlwidgets.knit_print_htmlwidget(interactive_plot, standalone=False)
    html = list(knitr_output)[0].replace('<!--html_preserve-->', '').replace('<!--/html_preserve-->', '')
    deps = base.attr(knitr_output, 'knit_meta')
    javascript = ''
    css = ''
    for dep in deps:
        path = Path(list(dep.rx2('src').rx2('file'))[0])
        package = dep.rx2('package')
        if package:
            package_path = Path(base.system_file('', package=package)[0])
            path = package_path / path
        stylesheet = dep.rx2('stylesheet')
        if stylesheet:
            stylesheet = path / list(stylesheet)[0]
            if stylesheet.exists():
                content = stylesheet.read_text()
                css += f'{content}\n'
            else:
                print(f'{stylesheet} does not exist')
        script = dep.rx2('script')

        if script:
            script = path / list(script)[0]
            if script.exists():
                content = script.read_text()
                javascript += f'{content}\n\n'
            else:
                print(f'{script} does not exist')
    style = ''
    for arg in ['width', 'height']:
        value = getattr(args, arg)
        if value is not None:
            style += f'{arg}: {value}px;'
    invoker = (
        "let girafe = this.closest('.girafe');"
        "let scripts = girafe.querySelectorAll('script');"
        "scripts.forEach(function(script){ if (script.type == 'text/javascript') eval(script.innerHTML) });"
        "window.HTMLWidgets.staticRender();"
        "this.parentNode.removeChild(this)"
    )
    display(
        HTML(
            data=(
                f'<div class="girafe">'
                f'<script type="text/javascript">{javascript}</script>'
                f'<style type="text/css">{css}</style>'
                f'<div style="{style}">{html}</div>'
                f'<img src onerror="{invoker}">'
                f'</div>'
            )
        )
    )