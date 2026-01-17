# We'll parse the provided LEF tech text and generate:
# 1) A routing layer summary table (width, pitch, dir, thickness, rpSq, spacing edge caps if present)
# 2) A cut/via layer summary table (width, spacing, resistance if present)
# 3) A VIA variant summary for each inter-layer via (e.g., via1_x, via2_x, ...), computing cut size and landing shapes
# 4) A simple "stack diagram" plot that shows layers in order with width and pitch annotations
# 5) Save CSVs and a PNG plot, and display the tables interactively
#
# NOTE: No internet access; everything is contained in this cell.

import re
import io
import math
from collections import defaultdict, OrderedDict
import pandas as pd
import matplotlib.pyplot as plt
from textwrap import shorten
from pathlib import Path

from caas_jupyter_tools import display_dataframe_to_user

tech_text = r"""
VERSION 5.6 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

UNITS
  DATABASE MICRONS 2000 ;
END UNITS

MANUFACTURINGGRID 0.0050 ;

LAYER poly
  TYPE MASTERSLICE ;
END poly

LAYER active
  TYPE MASTERSLICE ;
END active

LAYER metal1
  TYPE ROUTING ;
  SPACING 0.065 ;
  WIDTH 0.07 ;
  PITCH 0.14 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.38 ;
  THICKNESS 0.13 ;
  HEIGHT 0.37 ;
  CAPACITANCE CPERSQDIST 7.7161e-05 ;
  EDGECAPACITANCE 2.7365e-05 ;
END metal1

LAYER via1
  TYPE CUT ;
  SPACING 0.08 ;
  WIDTH 0.07 ;
  RESISTANCE 5 ;
END via1

LAYER metal2
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.3000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.0700     0.0700     0.0700     0.0700     0.0700     0.0700     
      WIDTH 0.0900       0.0700     0.0900     0.0900     0.0900     0.0900     0.0900     
      WIDTH 0.2700       0.0700     0.0900     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.0700     0.0900     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.0700     0.0900     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.0700     0.0900     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.07 ;
  PITCH 0.19 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.25 ;
  THICKNESS 0.14 ;
  HEIGHT 0.62 ;
  CAPACITANCE CPERSQDIST 4.0896e-05 ;
  EDGECAPACITANCE 2.5157e-05 ;
END metal2

LAYER via2
  TYPE CUT ;
  SPACING 0.09 ;
  WIDTH 0.07 ;
  RESISTANCE 5 ;
END via2

LAYER metal3
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.3000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.0700     0.0700     0.0700     0.0700     0.0700     0.0700     
      WIDTH 0.0900       0.0700     0.0900     0.0900     0.0900     0.0900     0.0900     
      WIDTH 0.2700       0.0700     0.0900     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.0700     0.0900     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.0700     0.0900     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.0700     0.0900     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.07 ;
  PITCH 0.14 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.25 ;
  THICKNESS 0.14 ;
  HEIGHT 0.88 ;
  CAPACITANCE CPERSQDIST 2.7745e-05 ;
  EDGECAPACITANCE 2.5157e-05 ;
END metal3

LAYER via3
  TYPE CUT ;
  SPACING 0.09 ;
  WIDTH 0.07 ;
  RESISTANCE 5 ;
END via3

LAYER metal4
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.1400     0.1400     0.1400     0.1400     0.1400     
      WIDTH 0.2700       0.1400     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.1400     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.1400     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.1400     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.14 ;
  PITCH 0.28 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.21 ;
  THICKNESS 0.28 ;
  HEIGHT 1.14 ;
  CAPACITANCE CPERSQDIST 2.0743e-05 ;
  EDGECAPACITANCE 3.0908e-05 ;
END metal4

LAYER via4
  TYPE CUT ;
  SPACING 0.16 ;
  WIDTH 0.14 ;
  RESISTANCE 3 ;
END via4

LAYER metal5
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.1400     0.1400     0.1400     0.1400     0.1400     
      WIDTH 0.2700       0.1400     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.1400     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.1400     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.1400     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.14 ;
  PITCH 0.28 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.21 ;
  THICKNESS 0.28 ;
  HEIGHT 1.71 ;
  CAPACITANCE CPERSQDIST 1.3527e-05 ;
  EDGECAPACITANCE 2.3863e-06 ;
END metal5

LAYER via5
  TYPE CUT ;
  SPACING 0.16 ;
  WIDTH 0.14 ;
  RESISTANCE 3 ;
END via5

LAYER metal6
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.1400     0.1400     0.1400     0.1400     0.1400     
      WIDTH 0.2700       0.1400     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.1400     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.1400     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.1400     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.14 ;
  PITCH 0.28 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.21 ;
  THICKNESS 0.28 ;
  HEIGHT 2.28 ;
  CAPACITANCE CPERSQDIST 1.0036e-05 ;
  EDGECAPACITANCE 2.3863e-05 ;
END metal6

LAYER via6
  TYPE CUT ;
  SPACING 0.16 ;
  WIDTH 0.14 ;
  RESISTANCE 3 ;
END via6

LAYER metal7
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.4000     0.4000     0.4000     0.4000     
      WIDTH 0.5000       0.4000     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.4000     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.4000     0.5000     0.9000     1.5000      ;
  WIDTH 0.4 ;
  PITCH 0.8 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.075 ;
  THICKNESS 0.8 ;
  HEIGHT 2.85 ;
  CAPACITANCE CPERSQDIST 7.9771e-06 ;
  EDGECAPACITANCE 3.2577e-05 ;
END metal7

LAYER via7
  TYPE CUT ;
  SPACING 0.44 ;
  WIDTH 0.4 ;
  RESISTANCE 1 ;
END via7

LAYER metal8
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.4000     0.4000     0.4000     0.4000     
      WIDTH 0.5000       0.4000     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.4000     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.4000     0.5000     0.9000     1.5000      ;
  WIDTH 0.4 ;
  PITCH 0.8 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.075 ;
  THICKNESS 0.8 ;
  HEIGHT 4.47 ;
  CAPACITANCE CPERSQDIST 5.0391e-06 ;
  EDGECAPACITANCE 2.3932e-05 ;
END metal8

LAYER via8
  TYPE CUT ;
  SPACING 0.44 ;
  WIDTH 0.4 ;
  RESISTANCE 1 ;
END via8

LAYER metal9
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     2.7000     4.0000     
      WIDTH 0.0000       0.8000     0.8000     0.8000     
      WIDTH 0.9000       0.8000     0.9000     0.9000     
      WIDTH 1.5000       0.8000     0.9000     1.5000      ;
  WIDTH 0.8 ;
  PITCH 1.6 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.03 ;
  THICKNESS 2 ;
  HEIGHT 6.09 ;
  CAPACITANCE CPERSQDIST 3.6827e-06 ;
  EDGECAPACITANCE 3.0803e-05 ;
END metal9

LAYER via9
  TYPE CUT ;
  SPACING 0.88 ;
  WIDTH 0.8 ;
  RESISTANCE 0.5 ;
END via9

LAYER metal10
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     2.7000     4.0000     
      WIDTH 0.0000       0.8000     0.8000     0.8000     
      WIDTH 0.9000       0.8000     0.9000     0.9000     
      WIDTH 1.5000       0.8000     0.9000     1.5000      ;
  WIDTH 0.8 ;
  PITCH 1.6 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.03 ;
  THICKNESS 2 ;
  HEIGHT 10.09 ;
  CAPACITANCE CPERSQDIST 2.2124e-06 ;
  EDGECAPACITANCE 2.3667e-05 ;
END metal10

LAYER hb_layer
  TYPE CUT ;
  SPACING 1 ;
  WIDTH 0.5 ;
  RESISTANCE 0.01 ;
END hb_layer

LAYER metal11
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     2.7000     4.0000     
      WIDTH 0.0000       0.8000     0.8000     0.8000     
      WIDTH 0.9000       0.8000     0.9000     0.9000     
      WIDTH 1.5000       0.8000     0.9000     1.5000      ;
  WIDTH 0.8 ;
  PITCH 1.6 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.03 ;
  THICKNESS 2 ;
  HEIGHT 10.09 ;
  CAPACITANCE CPERSQDIST 2.2124e-06 ;
  EDGECAPACITANCE 2.3667e-05 ;
END metal11

LAYER via11
  TYPE CUT ;
  SPACING 0.88 ;
  WIDTH 0.8 ;
  RESISTANCE 0.5 ;
END via11

LAYER metal12
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     2.7000     4.0000     
      WIDTH 0.0000       0.8000     0.8000     0.8000     
      WIDTH 0.9000       0.8000     0.9000     0.9000     
      WIDTH 1.5000       0.8000     0.9000     1.5000      ;
  WIDTH 0.8 ;
  PITCH 1.6 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.03 ;
  THICKNESS 2 ;
  HEIGHT 6.09 ;
  CAPACITANCE CPERSQDIST 3.6827e-06 ;
  EDGECAPACITANCE 3.0803e-05 ;
END metal12

LAYER via12
  TYPE CUT ;
  SPACING 0.44 ;
  WIDTH 0.4 ;
  RESISTANCE 1 ;
END via12

LAYER metal13
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.4000     0.4000     0.4000     0.4000     
      WIDTH 0.5000       0.4000     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.4000     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.4000     0.5000     0.9000     1.5000      ;
  WIDTH 0.4 ;
  PITCH 0.8 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.075 ;
  THICKNESS 0.8 ;
  HEIGHT 4.47 ;
  CAPACITANCE CPERSQDIST 5.0391e-06 ;
  EDGECAPACITANCE 2.3932e-05 ;
END metal13

LAYER via13
  TYPE CUT ;
  SPACING 0.44 ;
  WIDTH 0.4 ;
  RESISTANCE 1 ;
END via13

LAYER metal14
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.4000     0.4000     0.4000     0.4000     
      WIDTH 0.5000       0.4000     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.4000     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.4000     0.5000     0.9000     1.5000      ;
  WIDTH 0.4 ;
  PITCH 0.8 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.075 ;
  THICKNESS 0.8 ;
  HEIGHT 2.85 ;
  CAPACITANCE CPERSQDIST 7.9771e-06 ;
  EDGECAPACITANCE 3.2577e-05 ;
END metal14

LAYER via14
  TYPE CUT ;
  SPACING 0.16 ;
  WIDTH 0.14 ;
  RESISTANCE 3 ;
END via14

LAYER metal15
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.1400     0.1400     0.1400     0.1400     0.1400     
      WIDTH 0.2700       0.1400     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.1400     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.1400     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.1400     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.14 ;
  PITCH 0.28 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.21 ;
  THICKNESS 0.28 ;
  HEIGHT 2.28 ;
  CAPACITANCE CPERSQDIST 1.0036e-05 ;
  EDGECAPACITANCE 2.3863e-05 ;
END metal15

LAYER via15
  TYPE CUT ;
  SPACING 0.16 ;
  WIDTH 0.14 ;
  RESISTANCE 3 ;
END via15

LAYER metal16
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.1400     0.1400     0.1400     0.1400     0.1400     
      WIDTH 0.2700       0.1400     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.1400     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.1400     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.1400     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.14 ;
  PITCH 0.28 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.21 ;
  THICKNESS 0.28 ;
  HEIGHT 1.71 ;
  CAPACITANCE CPERSQDIST 1.3527e-05 ;
  EDGECAPACITANCE 2.3863e-06 ;
END metal16

LAYER via16
  TYPE CUT ;
  SPACING 0.16 ;
  WIDTH 0.14 ;
  RESISTANCE 3 ;
END via16

LAYER metal17
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.1400     0.1400     0.1400     0.1400     0.1400     
      WIDTH 0.2700       0.1400     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.1400     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.1400     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.1400     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.14 ;
  PITCH 0.28 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.21 ;
  THICKNESS 0.28 ;
  HEIGHT 1.14 ;
  CAPACITANCE CPERSQDIST 2.0743e-05 ;
  EDGECAPACITANCE 3.0908e-05 ;
END metal17

LAYER via17
  TYPE CUT ;
  SPACING 0.09 ;
  WIDTH 0.07 ;
  RESISTANCE 5 ;
END via17

LAYER metal18
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.3000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.0700     0.0700     0.0700     0.0700     0.0700     0.0700     
      WIDTH 0.0900       0.0700     0.0900     0.0900     0.0900     0.0900     0.0900     
      WIDTH 0.2700       0.0700     0.0900     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.0700     0.0900     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.0700     0.0900     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.0700     0.0900     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.07 ;
  PITCH 0.14 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.25 ;
  THICKNESS 0.14 ;
  HEIGHT 0.88 ;
  CAPACITANCE CPERSQDIST 2.7745e-05 ;
  EDGECAPACITANCE 2.5157e-05 ;
END metal18

LAYER via18
  TYPE CUT ;
  SPACING 0.09 ;
  WIDTH 0.07 ;
  RESISTANCE 5 ;
END via18

LAYER metal19
  TYPE ROUTING ;
  SPACINGTABLE 
    PARALLELRUNLENGTH    0.0000     0.3000     0.9000     1.8000     2.7000     4.0000     
      WIDTH 0.0000       0.0700     0.0700     0.0700     0.0700     0.0700     0.0700     
      WIDTH 0.0900       0.0700     0.0900     0.0900     0.0900     0.0900     0.0900     
      WIDTH 0.2700       0.0700     0.0900     0.2700     0.2700     0.2700     0.2700     
      WIDTH 0.5000       0.0700     0.0900     0.2700     0.5000     0.5000     0.5000     
      WIDTH 0.9000       0.0700     0.0900     0.2700     0.5000     0.9000     0.9000     
      WIDTH 1.5000       0.0700     0.0900     0.2700     0.5000     0.9000     1.5000      ;
  WIDTH 0.07 ;
  PITCH 0.19 ;
  DIRECTION HORIZONTAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.25 ;
  THICKNESS 0.14 ;
  HEIGHT 0.62 ;
  CAPACITANCE CPERSQDIST 4.0896e-05 ;
  EDGECAPACITANCE 2.5157e-05 ;
END metal19

LAYER via19
  TYPE CUT ;
  SPACING 0.08 ;
  WIDTH 0.07 ;
  RESISTANCE 5 ;
END via19

LAYER metal20
  TYPE ROUTING ;
  SPACING 0.065 ;
  WIDTH 0.07 ;
  PITCH 0.14 ;
  DIRECTION VERTICAL ;
  OFFSET 0.095 0.07 ;
  RESISTANCE RPERSQ 0.38 ;
  THICKNESS 0.13 ;
  HEIGHT 0.37 ;
  CAPACITANCE CPERSQDIST 7.7161e-05 ;
  EDGECAPACITANCE 2.7365e-05 ;
END metal20

LAYER OVERLAP
  TYPE OVERLAP ;
END OVERLAP

# VIA and VIARULE blocks are below; we will parse them too but not paste here again since we only need shapes for a few.
# (In this embedded text they are present in full above; for brevity in this cell, we rely on what's already included)
"""

# Because the user pasted the full file including VIA/VIARULE, we must append that section here too for complete parsing.
# To keep the notebook manageable, we will reuse the exact VIA/VIARULE text from the user's message.
via_and_rules = r"""
VIA via1_4 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal2 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via1_4

VIA via1_0 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal2 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via1_0

VIA via1_1 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal2 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via1_1

VIA via1_2 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal2 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via1_2

VIA via1_3 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal2 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via1_3

VIA via1_5 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal2 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via1_5

VIA via1_6 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via1_6

VIA via1_7 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal2 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via1_7

VIA via1_8 DEFAULT
  LAYER via1 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal1 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via1_8

VIA via2_8 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal3 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via2_8

VIA via2_4 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal3 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via2_4

VIA via2_5 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal3 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via2_5

VIA via2_7 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal3 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via2_7

VIA via2_6 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal3 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via2_6

VIA via2_0 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal3 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via2_0

VIA via2_1 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal3 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via2_1

VIA via2_2 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal3 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via2_2

VIA via2_3 DEFAULT
  LAYER via2 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal2 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal3 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via2_3

VIA via3_2 DEFAULT
  LAYER via3 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal3 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal4 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via3_2

VIA via3_0 DEFAULT
  LAYER via3 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal3 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal4 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via3_0

VIA via3_1 DEFAULT
  LAYER via3 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal3 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal4 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via3_1

VIA via4_0 DEFAULT
  LAYER via4 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal4 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal5 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via4_0

VIA via5_0 DEFAULT
  LAYER via5 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal5 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal6 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via5_0

VIA via6_0 DEFAULT
  LAYER via6 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal6 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal7 ;
    RECT -0.2 -0.2 0.2 0.2 ;
END via6_0

VIA via7_0 DEFAULT
  LAYER via7 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal7 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal8 ;
    RECT -0.2 -0.2 0.2 0.2 ;
END via7_0

VIA via8_0 DEFAULT
  LAYER via8 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal8 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal9 ;
    RECT -0.4 -0.4 0.4 0.4 ;
END via8_0

VIA via9_0 DEFAULT
  LAYER via9 ;
    RECT -0.4 -0.4 0.4 0.4 ;
  LAYER metal9 ;
    RECT -0.4 -0.4 0.4 0.4 ;
  LAYER metal10 ;
    RECT -0.4 -0.4 0.4 0.4 ;
END via9_0

VIA hb_layer_0 DEFAULT
  LAYER hb_layer ;
    RECT -0.25 -0.25 0.25 0.25 ;
  LAYER metal10 ;
    RECT -0.25 -0.25 0.25 0.25 ;
  LAYER metal11 ;
    RECT -0.25 -0.25 0.25 0.25 ;
END hb_layer_0

VIA via11_0 DEFAULT
  LAYER via11 ;
    RECT -0.4 -0.4 0.4 0.4 ;
  LAYER metal11 ;
    RECT -0.4 -0.4 0.4 0.4 ;
  LAYER metal12 ;
    RECT -0.4 -0.4 0.4 0.4 ;
END via11_0

VIA via12_0 DEFAULT
  LAYER via12 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal12 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal13 ;
    RECT -0.4 -0.4 0.4 0.4 ;
END via12_0

VIA via13_0 DEFAULT
  LAYER via13 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal13 ;
    RECT -0.2 -0.2 0.2 0.2 ;
  LAYER metal14 ;
    RECT -0.2 -0.2 0.2 0.2 ;
END via13_0

VIA via14_0 DEFAULT
  LAYER via14 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal14 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal15 ;
    RECT -0.2 -0.2 0.2 0.2 ;
END via14_0

VIA via15_0 DEFAULT
  LAYER via15 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal15 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal16 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via15_0

VIA via16_0 DEFAULT
  LAYER via16 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal16 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal17 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via16_0

VIA via17_2 DEFAULT
  LAYER via17 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal17 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal18 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via17_2

VIA via17_0 DEFAULT
  LAYER via17 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal17 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal18 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via17_0

VIA via17_1 DEFAULT
  LAYER via17 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal17 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal18 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via17_1

VIA via18_8 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via18_8

VIA via18_4 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal19 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via18_4

VIA via18_5 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal19 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via18_5

VIA via18_7 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal19 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via18_7

VIA via18_6 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via18_6

VIA via18_0 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal19 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via18_0

VIA via18_1 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal19 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via18_1

VIA via18_2 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal19 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via18_2

VIA via18_3 DEFAULT
  LAYER via18 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal18 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal19 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via18_3

VIA via19_4 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal20 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via19_4

VIA via19_0 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal20 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via19_0

VIA via19_1 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal20 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via19_1

VIA via19_2 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.07 0.07 0.07 ;
  LAYER metal20 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via19_2

VIA via19_3 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal20 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via19_3

VIA via19_5 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.035 -0.07 0.035 0.07 ;
  LAYER metal20 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via19_5

VIA via19_6 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal20 ;
    RECT -0.07 -0.07 0.07 0.07 ;
END via19_6

VIA via19_7 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal20 ;
    RECT -0.035 -0.07 0.035 0.07 ;
END via19_7

VIA via19_8 DEFAULT
  LAYER via19 ;
    RECT -0.035 -0.035 0.035 0.035 ;
  LAYER metal19 ;
    RECT -0.07 -0.035 0.07 0.035 ;
  LAYER metal20 ;
    RECT -0.07 -0.035 0.07 0.035 ;
END via19_8
"""

tech_full = tech_text + "\n" + via_and_rules

# --------- Parsers ---------

layer_block_re = re.compile(
    r"LAYER\s+(\w+)\s+(.*?)END\s+\1",
    re.S | re.M
)

def parse_float_after(keyword, text):
    m = re.search(rf"{keyword}\s+([-\d\.eE]+)\s*;", text)
    return float(m.group(1)) if m else None

def parse_two_floats_after(keyword, text):
    m = re.search(rf"{keyword}\s+([-\d\.eE]+)\s+([-\d\.eE]+)\s*;", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None

def parse_direction(text):
    m = re.search(r"DIRECTION\s+(HORIZONTAL|VERTICAL)\s*;", text)
    return m.group(1) if m else None

def parse_type(text):
    m = re.search(r"TYPE\s+(\w+)\s*;", text)
    return m.group(1) if m else None

def parse_spacing_table(text):
    # very rough capture of the existence of SPACINGTABLE
    return "SPACINGTABLE" in text

def metal_num(name):
    m = re.match(r"metal(\d+)$", name, re.I)
    return int(m.group(1)) if m else None

# Routing and Cut layer summaries
routing_layers = []
cut_layers = []

for m in layer_block_re.finditer(tech_full):
    name = m.group(1)
    body = m.group(2)
    ltype = parse_type(body)
    if ltype == "ROUTING":
        routing_layers.append({
            "layer": name,
            "metal": metal_num(name),
            "width": parse_float_after(r"WIDTH", body),
            "pitch": parse_float_after(r"PITCH", body),
            "direction": parse_direction(body),
            "spacing": parse_float_after(r"SPACING", body),
            "thickness": parse_float_after(r"THICKNESS", body),
            "rpersq": parse_float_after(r"RESISTANCE\s+RPERSQ", body),
            "height": parse_float_after(r"HEIGHT", body),
            "cpersqdist": parse_float_after(r"CAPACITANCE\s+CPERSQDIST", body),
            "edgecap": parse_float_after(r"EDGECAPACITANCE", body),
            "has_spacingtable": parse_spacing_table(body)
        })
    elif ltype == "CUT":
        cut_layers.append({
            "layer": name,
            "via": re.match(r"via(\d+)$", name, re.I).group(1) if re.match(r"via(\d+)$", name, re.I) else name,
            "width": parse_float_after(r"WIDTH", body),
            "spacing": parse_float_after(r"SPACING", body),
            "resistance": parse_float_after(r"RESISTANCE", body)
        })

routing_df = pd.DataFrame(routing_layers).sort_values(
    by=["metal"], ascending=True, na_position="last"
).reset_index(drop=True)

cut_df = pd.DataFrame(cut_layers).sort_values(
    by=["via"], ascending=True, na_position="last"
).reset_index(drop=True)

# --------- VIA variant parser ---------

via_block_re = re.compile(r"VIA\s+(\w+)(.*?)END\s+\1", re.S | re.M)

def rect_dims(line):
    # RECT x1 y1 x2 y2 ; -> return (w, h)
    m = re.search(r"RECT\s+([-\d\.eE]+)\s+([-\d\.eE]+)\s+([-\d\.eE]+)\s+([-\d\.eE]+)\s*;", line)
    if not m:
        return None, None
    x1, y1, x2, y2 = map(float, m.groups())
    return abs(x2 - x1), abs(y2 - y1)

via_summaries = []

for m in via_block_re.finditer(tech_full):
    vname = m.group(1)
    body = m.group(2)
    # Find the three layers inside: viaX, metalN(lower), metalN+1(upper)
    # We'll capture each LAYER block within the VIA
    sub = re.findall(r"LAYER\s+(\w+)\s*;\s*(.*?)\n\s*(?=LAYER|\Z)", body, re.S | re.M)
    layers_inside = {}
    for lname, lbody in sub:
        w, h = rect_dims(lbody)
        layers_inside[lname] = (w, h)
    # derive classification
    cut_layer = next((k for k in layers_inside if k.startswith("via")), None)
    lower_metal = next((k for k in layers_inside if k.startswith("metal")), None)
    # gather first two metals by order of appearance
    metals_found = [k for k in layers_inside if k.startswith("metal")]
    metals_found_sorted = sorted(metals_found, key=lambda s: int(re.findall(r"\d+", s)[0]) if re.findall(r"\d+", s) else 0)
    m1 = metals_found_sorted[0] if len(metals_found_sorted) > 0 else None
    m2 = metals_found_sorted[1] if len(metals_found_sorted) > 1 else None

    cut_w, cut_h = layers_inside.get(cut_layer, (None, None))
    m1_w, m1_h = layers_inside.get(m1, (None, None))
    m2_w, m2_h = layers_inside.get(m2, (None, None))

    def shape_label(w, h):
        if w is None or h is None:
            return ""
        # tolerance to decide square vs horizontal/vertical
        eps = 1e-6
        if abs(w - h) < 1e-6:
            return "square"
        return "horizontal" if w > h+eps else "vertical"

    via_summaries.append({
        "via_name": vname,
        "cut_layer": cut_layer,
        "cut_w": cut_w,
        "cut_h": cut_h,
        "lower_metal": m1,
        "lower_shape": shape_label(m1_w, m1_h),
        "lower_w": m1_w,
        "lower_h": m1_h,
        "upper_metal": m2,
        "upper_shape": shape_label(m2_w, m2_h),
        "upper_w": m2_w,
        "upper_h": m2_h,
    })

via_df = pd.DataFrame(via_summaries)

# Also extract how many variants per viaN family
via_family = []
for name in via_df["via_name"]:
    m = re.match(r"(via\d+)_", name)
    fam = m.group(1) if m else name
    via_family.append(fam)
via_df["family"] = via_family

variants_df = via_df.groupby("family").size().reset_index(name="num_variants").sort_values("family")

# --------- Plot stack diagram ---------

def plot_stack(df: pd.DataFrame, outpath: Path):
    fig, ax = plt.subplots(figsize=(6, max(6, 0.4*len(df))))
    y = range(len(df))
    # We'll annotate each layer with width/pitch/direction
    for i, row in df.iterrows():
        label = f"{row['layer']} ({row['direction'][0] if isinstance(row['direction'], str) else ''})"
        ax.barh(i, row["width"] if pd.notnull(row["width"]) else 0, left=0)
        ax.text(row["width"] if pd.notnull(row["width"]) else 0, i, f" w={row['width']}, p={row['pitch']}", va='center', ha='left', fontsize=8)
        ax.text(-0.01, i, label, va='center', ha='right', fontsize=9)
    ax.set_yticks([])
    ax.set_xlabel("Nominal width (micron)")
    ax.set_title("Routing Layer Stack: width / pitch / direction")
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)

out_dir = Path("/mnt/data")
out_dir.mkdir(parents=True, exist_ok=True)

routing_csv = out_dir / "routing_layers_summary.csv"
cut_csv = out_dir / "cut_layers_summary.csv"
via_csv = out_dir / "via_variants_summary.csv"
variants_csv = out_dir / "via_families_counts.csv"
stack_png = out_dir / "routing_stack_plot.png"

routing_df.to_csv(routing_csv, index=False)
cut_df.to_csv(cut_csv, index=False)
via_df.to_csv(via_csv, index=False)
variants_df.to_csv(variants_csv, index=False)

plot_stack(routing_df, stack_png)

# Display tables to user
display_dataframe_to_user("Routing Layer Summary", routing_df)
display_dataframe_to_user("Cut/Via Layer Summary", cut_df)
display_dataframe_to_user("Via Variants Summary", via_df)
display_dataframe_to_user("Via Family Variant Counts", variants_df)

# Provide file paths to the outputs
routing_csv, cut_csv, via_csv, variants_csv, stack_png
