#-*- coding:utf-8 -*-

import os

activate_this = '%s/env/bin/activate_this.py' % os.path.dirname(os.path.abspath(__file__))
execfile(activate_this, dict(__file__=activate_this))

from past import app
#app.run(port=80)

if __name__ == "__main__":
    app.run(port=80)
