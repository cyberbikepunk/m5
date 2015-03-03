"""  All plot making with matplotlib is found here. """

import numpy as np
import matplotlib.pyplot as plt
import os
import plotly.plotly as py
from plotly.graph_objs import *


def bar_plot(ax, df):
    pass
    n_groups = 5

    means_men = (20, 35, 30, 35, 27)
    std_men = (2, 3, 4, 1, 2)

    means_women = (25, 32, 34, 20, 25)
    std_women = (3, 5, 2, 3, 3)

    fig, ax = plt.subplots()

    index = np.arange(n_groups)
    bar_width = 0.35

    opacity = 0.4
    error_config = {'ecolor': '0.3'}

    rects1 = plt.bar(df.columns.values, means_men, bar_width,
                     alpha=opacity,
                     color='b',
                     yerr=std_men,
                     error_kw=error_config,
                     label='Men')

    rects2 = plt.bar(index + bar_width, means_women, bar_width,
                     alpha=opacity,
                     color='r',
                     yerr=std_women,
                     error_kw=error_config,
                     label='Women')

    plt.xlabel('Group')
    plt.ylabel('Scores')
    plt.title('Scores by group and gender')
    plt.xticks(index + bar_width, ('A', 'B', 'C', 'D', 'E'))
    plt.legend()

    plt.tight_layout()
    plt.show()


def get_next_filename(output_folder):
    highest_nb = 0
    for f in os.listdir(output_folder):
        if os.path.isfile(os.path.join(output_folder, f)):
            filename = os.path.splitext(f)[0]
            try:
                file_num = int(filename)
                if file_num > highest_nb:
                    highest_nb = file_num
            except ValueError:
                'The file name "%s" is not an integer. Skipping' % filename

    next_filename = os.path.join(output_folder, str(highest_nb + 1))
    return next_filename