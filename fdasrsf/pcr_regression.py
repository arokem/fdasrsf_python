"""
Warping PCR Invariant Regression using SRSF

moduleauthor:: Derek Tucker <jdtuck@sandia.gov>

"""

import numpy as np
import fdasrsf as fs
import fdasrsf.utility_functions as uf
import fdasrsf.fPCA as fpca
from scipy import dot
from scipy.linalg import inv, norm


def elastic_pcr_regression(f, y, time, pca_method="combined", no=5, 
                           smooth_data=False, sparam=25, parallel=False, 
                           C=None):
    """
    This function identifies a regression model with phase-variability
    using elastic pca

    :param f: numpy ndarray of shape (M,N) of N functions with M samples
    :param y: numpy array of N responses
    :param time: vector of size M describing the sample points
    :param pca_method: string specifing pca method (options = "combined",
                       "vert", or "horiz", default = "combined")
    :param no: scalar specify number of principal components (default=5)
    :param smooth_data: smooth data using box filter (default = F)
    :param sparam: number of times to apply box filter (default = 25)
    :param parallel: run in parallel (default = F)
    :param C: scale balance parameter for combined method (default = None)
    :type f: np.ndarray
    :type time: np.ndarray

    :rtype: tuple of numpy array
    :return alpha: alpha parameter of model
    :return b: regressor vector
    :return y: response vector
    :return warp_data: alignment object from srsf_align
    :return pca: fpca object from corresponding pca method
    :return SSE: sum of squared errors
    :return b: basis coefficients
    :return pca.method: string of pca method

    """

    if smooth_data:
        f = fs.smooth_data(f,sparam)
    
    N1 = f.shape[1]

    # Align Data
    out = fs.srsf_align(f, time, showplot=False, parallel=parallel)

    # Calculate PCA
    if pca_method=='combined':
        out_pca = fpca.jointfPCA(out.fn, time, out.qn, out.q0, out.gam, no, showplot=False)
    elif pca_method=='vert':
        out_pca = fpca.vertfPCA(out.fn, time, out.qn, no, showplot=False)
    elif pca_method=='horiz':
        out_pca = fpca.horizfPCA(out.gam, time, no, showplot=False)
    else:
        raise Exception('Invalid fPCA Method')
    
    # OLS using PCA basis
    lam = 0
    R = 0
    Phi = np.ones((N1, no+1))
    Phi[:,1:(no+1)] = out_pca.coef
    xx = dot(Phi.T, Phi)
    inv_xx = inv(xx + lam * R)
    xy = dot(Phi.T, y)
    b = dot(inv_xx, xy)
    alpha = b[0]
    b = b[1:no+1]

    # compute the SSE
    int_X = np.zeros(N1)
    for ii in range(0,N1):
        int_X[ii] = np.sum(out_pca.coef*b)
    
    SSE = np.sum((y-alpha-int_X)**2)

    efpcr_results = collections.namedtuple('efpcr', ['alpha', 'b', 'y', 'warp_data', 'pca', 'SSE', 'pca_method'])
    efpcr = efpcr_results(alpha, b, y, out, out_pca, SSE, pca_method)

    return efpcr
        

