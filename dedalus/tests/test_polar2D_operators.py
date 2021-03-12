"""Disk and annulus tests for convert, interpolate."""

import pytest
import numpy as np
from dedalus.core import coords, distributor, basis, field, operators, arithmetic
from dedalus.tools.cache import CachedFunction


Nphi_range = [8]
Nr_range = [8]
k_range = [0, 1]
dealias_range = [1, 3/2]
radius_disk = 1.5
radii_annulus = (0.5, 3)


@CachedFunction
def build_disk(Nphi, Nr, k, dealias, dtype):
    c = coords.PolarCoordinates('phi', 'r')
    d = distributor.Distributor((c,))
    b = basis.DiskBasis(c, (Nphi, Nr), radius=radius_disk, k=k, dealias=(dealias, dealias), dtype=dtype)
    phi, r = b.local_grids(b.domain.dealias)
    x, y = c.cartesian(phi, r)
    return c, d, b, phi, r, x, y


@CachedFunction
def build_annulus(Nphi, Nr, k, dealias, dtype):
    c = coords.PolarCoordinates('phi', 'r')
    d = distributor.Distributor((c,))
    b = basis.AnnulusBasis(c, (Nphi, Nr), radii=radii_annulus, k=k, dealias=(dealias, dealias), dtype=dtype)
    phi, r = b.local_grids(b.domain.dealias)
    x, y = c.cartesian(phi, r)
    return c, d, b, phi, r, x, y


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_spherical_ell_product_scalar(Nphi, Ntheta, Nr, k, dealias, basis, dtype):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     f = field.Field(dist=d, bases=(b,), dtype=dtype)
#     g = field.Field(dist=d, bases=(b,), dtype=dtype)
#     f.set_scales(b.domain.dealias)
#     f['g'] = 3*x**2 + 2*y*z
#     for ell, m_ind, ell_ind in b.ell_maps:
#         g['c'][m_ind, ell_ind, :] = (ell+3)*f['c'][m_ind, ell_ind, :]
#     func = lambda ell: ell+3
#     h = operators.SphericalEllProduct(f, c, func).evaluate()
#     g.set_scales(b.domain.dealias)
#     assert np.allclose(h['g'], g['g'])


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_spherical_ell_product_vector(Nphi, Ntheta, Nr, k, dealias, basis, dtype):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     f = field.Field(dist=d, bases=(b,), dtype=dtype)
#     f.set_scales(b.domain.dealias)
#     f['g'] = 3*x**2 + 2*y*z
#     u = operators.Gradient(f, c).evaluate()
#     uk0 = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     uk0.set_scales(b.domain.dealias)
#     uk0['g'] = u['g']
#     v = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     v.set_scales(b.domain.dealias)
#     for ell, m_ind, ell_ind in b.ell_maps:
#         v['c'][0, m_ind, ell_ind, :] = (ell+2)*uk0['c'][0, m_ind, ell_ind, :]
#         v['c'][1, m_ind, ell_ind, :] = (ell+4)*uk0['c'][1, m_ind, ell_ind, :]
#         v['c'][2, m_ind, ell_ind, :] = (ell+3)*uk0['c'][2, m_ind, ell_ind, :]
#     func = lambda ell: ell+3
#     w = operators.SphericalEllProduct(u, c, func).evaluate()
#     assert np.allclose(w['g'], v['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_disk, build_annulus])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('layout', ['c', 'g'])
def test_convert_scalar(Nphi, Nr, k, dealias, basis, dtype, layout):
    c, d, b, phi, r, x, y = basis(Nphi, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = 3*x**2 + 2*y
    g = operators.Laplacian(f, c).evaluate()
    f.require_layout(layout)
    g.require_layout(layout)
    h = (f + g).evaluate()
    assert np.allclose(h['g'], f['g'] + g['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_disk, build_annulus])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('layout', ['c', 'g'])
def test_convert_vector(Nphi, Nr, k, dealias, basis, dtype, layout):
    c, d, b, phi, r, x, y = basis(Nphi, Nr, k, dealias, dtype)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    u.set_scales(b.dealias)
    ex = np.array([-np.sin(phi)+0.*r,np.cos(phi)+0.*r])
    ey = np.array([np.cos(phi)+0.*r,np.sin(phi)+0.*r])
    u['g'] = 4*x**3*ey + 3*y**2*ey
    v = operators.Laplacian(u, c).evaluate()
    u.require_layout(layout)
    v.require_layout(layout)
    w = (u + v).evaluate()
    assert np.allclose(w['g'], u['g'] + v['g'])


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# @pytest.mark.parametrize('layout', ['c', 'g'])
# def test_trace_tensor(Nphi, Ntheta, Nr, k, dealias, basis, dtype, layout):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
#     u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     u.set_scales(b.domain.dealias)
#     u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
#     u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
#     u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
#     T = operators.Gradient(u, c).evaluate()
#     fg = T['g'][0,0] + T['g'][1,1] + T['g'][2,2]
#     T.require_layout(layout)
#     f = operators.Trace(T).evaluate()
#     assert np.allclose(f['g'], fg)


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# @pytest.mark.parametrize('layout', ['c', 'g'])
# def test_transpose_tensor(Nphi, Ntheta, Nr, k, dealias, dtype, basis, layout):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
#     u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     u.set_scales(b.domain.dealias)
#     u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
#     u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
#     u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
#     T = operators.Gradient(u, c).evaluate()
#     Tg = np.transpose(np.copy(T['g']),(1,0,2,3,4))
#     T.require_layout(layout)
#     T = operators.TransposeComponents(T).evaluate()
#     assert np.allclose(T['g'], Tg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Nr', [8])
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_disk, build_annulus])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_interpolation_scalar(Nphi, Nr, k, dealias, basis, dtype, radius):
    c, d, b, phi, r, x, y = basis(Nphi, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = x**4 + 2*y**4
    h = operators.interpolate(f, r=radius).evaluate()
    x0, y0 = c.cartesian(phi, np.array([[radius]]))
    hg = x0**4 + 2*y0**4
    assert np.allclose(h['g'], hg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Nr', [8])
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_disk, build_annulus])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_interpolation_vector(Nphi, Nr, k, dealias, basis, dtype, radius):
    c, d, b, phi, r, x, y = basis(Nphi, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = x**4 + 2*y**4
    u = operators.Gradient(f, c)
    v = u(r=radius).evaluate()
    x0, y0 = c.cartesian(phi, np.array([[radius]]))
    ex0 = np.array([-np.sin(phi)+0.*np.array([[radius]]),np.cos(phi)+0.*np.array([[radius]])])
    ey0 = np.array([np.cos(phi)+0.*np.array([[radius]]),np.sin(phi)+0.*np.array([[radius]])])
    vg = 4*x0**3*ex0 + 8*y0**3*ey0
    assert np.allclose(v['g'], vg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Nr', [8])
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_disk, build_annulus])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_interpolation_tensor(Nphi, Nr, k, dealias, basis, dtype, radius):
    c, d, b, phi, r, x, y = basis(Nphi, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = x**4 + 2*y**4
    u = operators.Gradient(f, c)
    T = operators.Gradient(u, c)
    v = T(r=radius).evaluate()
    x0, y0 = c.cartesian(phi, np.array([[radius]]))
    ex0 = np.array([-np.sin(phi)+0.*np.array([[radius]]),np.cos(phi)+0.*np.array([[radius]])])
    ey0 = np.array([np.cos(phi)+0.*np.array([[radius]]),np.sin(phi)+0.*np.array([[radius]])])
    exex0 = ex0[:,None, ...] * ex0[None,...]
    eyey0 = ey0[:,None, ...] * ey0[None,...]
    vg = 12*x0**2*exex0 + 24*y0**2*eyey0
    assert np.allclose(v['g'], vg)


# @pytest.mark.parametrize('Nphi', [16])
# @pytest.mark.parametrize('Ntheta', [8])
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# @pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
# def test_radial_component_vector(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
#     u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     u.set_scales(b.domain.dealias)
#     u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
#     u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
#     u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
#     v = operators.RadialComponent(operators.interpolate(u, r=radius)).evaluate()
#     vg = radius**2*st*(2*ct**2*cp-radius*ct**3*sp+radius**3*cp**3*st**5*sp**3+radius*ct*st**2*(cp**3+sp**3))
#     assert np.allclose(v['g'], vg)


# @pytest.mark.parametrize('Nphi', [16])
# @pytest.mark.parametrize('Ntheta', [8])
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# @pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
# def test_radial_component_tensor(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     T = field.Field(dist=d, bases=(b,), tensorsig=(c,c), dtype=dtype)
#     T.set_scales(b.domain.dealias)
#     T['g'][2,2] = (6*x**2+4*y*z)/r**2
#     T['g'][2,1] = T['g'][1,2] = -2*(y**3+x**2*(y-3*z)-y*z**2)/(r**3*np.sin(theta))
#     T['g'][2,0] = T['g'][0,2] = 2*x*(z-3*y)/(r**2*np.sin(theta))
#     T['g'][1,1] = 6*x**2/(r**2*np.sin(theta)**2) - (6*x**2+4*y*z)/r**2
#     T['g'][1,0] = T['g'][0,1] = -2*x*(x**2+y**2+3*y*z)/(r**3*np.sin(theta)**2)
#     T['g'][0,0] = 6*y**2/(x**2+y**2)
#     A = operators.RadialComponent(operators.interpolate(T, r=radius)).evaluate()
#     Ag = 0 * A['g']
#     Ag[2] = 2*np.sin(theta)*(3*np.cos(phi)**2*np.sin(theta)+2*np.cos(theta)*np.sin(phi))
#     Ag[1] = 6*np.cos(theta)*np.cos(phi)**2*np.sin(theta) + 2*np.cos(2*theta)*np.sin(phi)
#     Ag[0] = 2*np.cos(phi)*(np.cos(theta) - 3*np.sin(theta)*np.sin(phi))
#     assert np.allclose(A['g'], Ag)


# @pytest.mark.parametrize('Nphi', [16])
# @pytest.mark.parametrize('Ntheta', [8])
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# @pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
# def test_angular_component_vector(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
#     u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     u.set_scales(b.domain.dealias)
#     u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
#     u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
#     u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
#     v = operators.AngularComponent(operators.interpolate(u, r=radius)).evaluate()
#     vg = 0 * v['g']
#     vg[0] = radius**2*sp*(-2*ct**2+radius*ct*cp*st**2*sp-radius**3*cp**2*st**5*sp**3)
#     vg[1] = radius**2*(2*ct**3*cp-radius*cp**3*st**4+radius**3*ct*cp**3*st**5*sp**3-1/16*radius*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
#     assert np.allclose(v['g'], vg)


# @pytest.mark.parametrize('Nphi', [16])
# @pytest.mark.parametrize('Ntheta', [8])
# @pytest.mark.parametrize('Nr', Nr_range)
# @pytest.mark.parametrize('k', k_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_ball, build_shell])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# @pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
# def test_angular_component_tensor(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
#     c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
#     T = field.Field(dist=d, bases=(b,), tensorsig=(c,c), dtype=dtype)
#     T.set_scales(b.domain.dealias)
#     T['g'][2,2] = (6*x**2+4*y*z)/r**2
#     T['g'][2,1] = T['g'][1,2] = -2*(y**3+x**2*(y-3*z)-y*z**2)/(r**3*np.sin(theta))
#     T['g'][2,0] = T['g'][0,2] = 2*x*(z-3*y)/(r**2*np.sin(theta))
#     T['g'][1,1] = 6*x**2/(r**2*np.sin(theta)**2) - (6*x**2+4*y*z)/r**2
#     T['g'][1,0] = T['g'][0,1] = -2*x*(x**2+y**2+3*y*z)/(r**3*np.sin(theta)**2)
#     T['g'][0,0] = 6*y**2/(x**2+y**2)
#     A = operators.AngularComponent(operators.interpolate(T, r=radius), index=1).evaluate()
#     Ag = 0 * A['g']
#     Ag[2,1] = 6*np.cos(theta)*np.cos(phi)**2*np.sin(theta) + 2*np.cos(2*theta)*np.sin(phi)
#     Ag[2,0] = 2*np.cos(phi)*(np.cos(theta) - 3*np.sin(theta)*np.sin(phi))
#     Ag[1,1] = 2*np.cos(theta)*(3*np.cos(theta)*np.cos(phi)**2 - 2*np.sin(theta)*np.sin(phi))
#     Ag[1,0] = Ag[0,1] = -2*np.cos(phi)*(np.sin(theta) + 3*np.cos(theta)*np.sin(phi))
#     Ag[0,0] = 6*np.sin(phi)**2
#     assert np.allclose(A['g'], Ag)

