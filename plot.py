#!/usr/bin/env python
# coding: utf-8

import os, math, datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.plotting import figure, gridplot, output_file, save
from bokeh.models import Paragraph
import xml.etree.ElementTree as ET

import argparse
parser = argparse.ArgumentParser(description='Command line arguments')
parser.add_argument("-i", "--inputfile", action="store", type=str, dest="inputfile", default="TREVISO_GEMAC800_2P0P5_SNSJ414422127WA_resting_5_2021-04-28T00-48-39.xml", help="Specify input files")
parser.add_argument("-o", "--outputfile", action="store", type=str, dest="outputfile", default="test.html", help="Specify output file")
parser.add_argument("-v", "--verbose", action="store", type=int, default=0, dest="verbose", help="Specify verbosity level")
args = parser.parse_args()



tree = ET.parse(args.inputfile)
root = tree.getroot()
ns = root.tag.split('}')[0] + '}'

xUnit, xScale = 'Hz', 1000
for xPar in root.iter(ns + 'sampleRate'):
    xUnit, xScale = xPar.attrib['U'], float(xPar.attrib['V'])

yUnit, yScale = 'mm/s', 25
for yPar in root.iter(ns + 'writerSpeed'):
    yUnit, yScale = yPar.attrib['U'], float(yPar.attrib['V'])


ecg_dict = {}

for wav in root.iter(ns + 'wav'): # Look for waveforms only within the Wav tag (full record)
    for der in wav.iter(ns + 'ecgWaveform'):
        lead = der.attrib['lead']
        meas = der.attrib['V']
        ecg_dict[lead] = list(map(float, meas.split(" ")))

interpretation, diagnosis = "", ""
for inter in root.iter(ns + 'interpretation'):
    for stat in inter.iter(ns + 'statement'):
        interpretation += stat.attrib['V'] + " "

for inter in root.iter(ns + 'hookupAdvisor'):
    for stat in inter.iter(ns + 'statement'):
        diagnosis += stat.attrib['V'] + " "

print("Referto:\n", interpretation)
print("Diagnosi:\n", diagnosis)



df = pd.DataFrame().from_dict(ecg_dict)
derivations = df.columns


print(df.dtypes, df)


df = df.div(float(1000.))

df['T'] = df.index  / xScale


# Output to static HTML file
output_file(args.outputfile)

figs, texts = [], []

for der in derivations:
	fig = figure(width=1200, height=200, title="Derivazione " + der, x_axis_label="time (s)", y_axis_label="V (mV)", x_range=(0., np.max(df['T']) ), tools=['xpan', 'reset', 'save'])
	fig.line(df['T'], df[der], line_width=0.5)
	fig.sizing_mode = 'scale_width' # Scale plot width to page
	figs.append(fig)

for txt in [interpretation, diagnosis]:
    text = Paragraph(text = txt, width = 1200, height_policy = "auto", style = {'fontsize': '10pt', 'color': 'black', 'font-family': 'arial'})
    texts.append(text)

# Link together the x-axes
for ide, der in enumerate(derivations): figs[ide].x_range = figs[0].x_range

# Put the subplots in a gridplot
p = gridplot([[x] for x in figs + texts], toolbar_location=None)

# Show the results
save(p)

if args.verbose >= 0: print("Output saved to", args.outputfile)


