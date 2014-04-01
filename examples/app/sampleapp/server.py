from flask import Flask, render_template
from os.path import dirname, join, abspath
import logging
approot = abspath(dirname(dirname(__file__)))
app = Flask('sampleapp')
app.debug = True
import pandas as pd
from bokeh.pluginutils import app_document
from bokeh.plotting import output_server, session, circle
import numpy as np
from bokeh.objects import Range1d, ColumnDataSource

from sampleapp.objects import App
import uuid

@app_document("sampleapp")
def make_plot():
    sess = session()
    data = pd.DataFrame({'a'  : np.random.randn(100), 'b' : np.random.randn(100)})
    source = ColumnDataSource(data=data)
    scatter_plot = circle(source=source, x='a', y='b', plot_width=500, 
                         plot_height=500)
    app = App(data_source=source,
              scatter_plot=scatter_plot,
              stats=str(data.describe())
    )
    return app
        
@app.route("/app")
def main():
    app = make_plot()
    docname = session().docname
    return render_template('page.html', docname=docname)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.debug = True
    app.run(host='0.0.0.0', port=5050)