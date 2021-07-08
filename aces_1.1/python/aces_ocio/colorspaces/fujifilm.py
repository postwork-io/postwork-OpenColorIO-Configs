#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Implements support for *Fujifilm* colorspaces conversions and transfer functions.
"""

from __future__ import division

import array
import os

import PyOpenColorIO as ocio

import aces_ocio.generate_lut as genlut
from aces_ocio.utilities import ColorSpace, mat44_from_mat33

__author__ = 'Nathan Inglesby'
__license__ = ''
__maintainer__ = 'PostWork.io Developers'
__email__ = 'nate@postwork.io'
__status__ = 'Development'

__all__ = ['create_FLog', 'create_colorspaces']


def create_FLog(gamut, transfer_function, lut_directory, lut_resolution_1D,
                aliases):
    """
    Creates colorspace covering the conversion from *Fujifilm* spaces to *ACES*,
    with various transfer functions and encoding gamuts covered.

    Parameters
    ----------
    gamut : str
        The name of the encoding gamut to use.
    transfer_function : str
        The name of the transfer function to use.
    lut_directory : str or unicode 
        The directory to use when generating LUTs.
    lut_resolution_1D : int
        The resolution of generated 1D LUTs.
    aliases : list of str
        Aliases for this colorspace.

    Returns
    -------
    ColorSpace
         A ColorSpace container class referencing the LUTs, matrices and
         identifying information for the requested colorspace.
    """

    name = '{0} - {1}'.format(transfer_function, gamut)
    if transfer_function == '':
        name = 'Linear - {0}'.format(gamut)
    if gamut == '':
        name = 'Curve - {0}'.format(transfer_function)

    cs = ColorSpace(name)
    cs.description = name
    cs.aliases = aliases
    cs.equality_group = ''
    cs.family = 'Input/Fujifilm'
    cs.is_data = False

    if gamut and transfer_function:
        cs.aces_transform_id = 'IDT.Fujifilm.{0}_{1}_10i.a1.v1'.format(
            transfer_function.replace('-', ''),
            gamut.replace('-', '').replace(' ', '_'))

    # A linear space needs allocation variables.
    if transfer_function == '':
        cs.allocation_type = ocio.Constants.UNIFORM
        cs.allocation_vars = [0,1]

    def FLog_to_linear(f_log):
        a = 0.555556
        b = 0.009468
        c = 0.344676
        d = 0.790453
        e = 8.735631
        f = 0.092864
        cut1 = 0.00089
        cut2 = 0.100537775223865

        if f_log >= cut2:
            linear = pow(10., ((f_log - d) / c)) / a - b / a
                
        else:
            linear = (f_log - f) / e
        return linear


    cs.to_reference_transforms = []

    if transfer_function == 'F-Log':
        data = array.array('f', '\0' * lut_resolution_1D * 4)
        for c in range(lut_resolution_1D):
            data[c] = FLog_to_linear( c / (lut_resolution_1D - 1))

        lut = '{0}_to_linear.spi1d'.format(transfer_function)
        genlut.write_SPI_1D(
            os.path.join(lut_directory, lut), 0, 1, data, lut_resolution_1D, 1)

        cs.to_reference_transforms.append({
            'type': 'lutFile',
            'path': lut,
            'interpolation': 'linear',
            'direction': 'forward'
        })

    if gamut == 'F-Gamut':
        cs.to_reference_transforms.append({
            'type':
            'matrix',
            'matrix':
            mat44_from_mat33([
                0.678891150633901, 0.1588684223720231, 0.16224042703694286, 
                0.04557083089802189, 0.8607127720288463, 0.09371639707888578, 
                -0.00048571035183551524, 0.025060195736249565, 0.9754255146150821
            ]),
            'direction':
            'forward'
        })

    cs.from_reference_transforms = []
    return cs


def create_colorspaces(lut_directory, lut_resolution_1D):
    """
    Generates the colorspace conversions.

    Parameters
    ----------
    lut_directory : str or unicode 
        The directory to use when generating LUTs.
    lut_resolution_1D : int
        The resolution of generated 1D LUTs.

    Returns
    -------
    list
         A list of colorspaces for Sony cameras and encodings.
    """

    colorspaces = []

    
    f_log_f_gamut = create_FLog('F-Gamut', 'F-Log', lut_directory,
                                  lut_resolution_1D, ['flog_fgamut'])
    colorspaces.append(f_log_f_gamut)

    # Linearization Only
    f_log = create_FLog('', 'F-Log', lut_directory, lut_resolution_1D,
                         ['crv_flog'])
    colorspaces.append(f_log)

   

    return colorspaces
