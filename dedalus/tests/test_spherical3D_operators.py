"""Ball and shell tests for spherical_ell_product, convert, trace, transpose, interpolate, radial_component, angular_component."""

import pytest
import numpy as np
from dedalus.core import coords, distributor, basis, field, operators, arithmetic
from dedalus.tools.cache import CachedFunction


Nphi_range = [8]
Ntheta_range = [4]
Nr_range = [10]
k_range = [0, 1]
dealias_range = [1, 3/2]
radius_ball = 1.5
radii_shell = (0.5, 1.5)


@CachedFunction
def build_ball(Nphi, Ntheta, Nr, k, dealias, dtype):
    c = coords.SphericalCoordinates('phi', 'theta', 'r')
    d = distributor.Distributor((c,))
    b = basis.BallBasis(c, (Nphi, Ntheta, Nr), radius=radius_ball, k=k, dealias=(dealias, dealias, dealias), dtype=dtype)
    phi, theta, r = b.local_grids(b.domain.dealias)
    x, y, z = c.cartesian(phi, theta, r)
    return c, d, b, phi, theta, r, x, y, z


@CachedFunction
def build_shell(Nphi, Ntheta, Nr, k, dealias, dtype):
    c = coords.SphericalCoordinates('phi', 'theta', 'r')
    d = distributor.Distributor((c,))
    b = basis.SphericalShellBasis(c, (Nphi, Ntheta, Nr), radii=radii_shell, k=k, dealias=(dealias, dealias, dealias), dtype=dtype)
    phi, theta, r = b.local_grids(b.domain.dealias)
    x, y, z = c.cartesian(phi, theta, r)
    return c, d, b, phi, theta, r, x, y, z


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
def test_spherical_ell_product_scalar(Nphi, Ntheta, Nr, k, dealias, basis, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = 3*x**2 + 2*y*z
    for ell, m_ind, ell_ind in b.ell_maps:
        g['c'][m_ind, ell_ind, :] = (ell+3)*f['c'][m_ind, ell_ind, :]
    func = lambda ell: ell+3
    h = operators.SphericalEllProduct(f, c, func).evaluate()
    g.set_scales(b.domain.dealias)
    assert np.allclose(h['g'], g['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
def test_spherical_ell_product_vector(Nphi, Ntheta, Nr, k, dealias, basis, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = 3*x**2 + 2*y*z
    u = operators.Gradient(f, c).evaluate()
    uk0 = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    uk0.set_scales(b.domain.dealias)
    uk0['g'] = u['g']
    v = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    v.set_scales(b.domain.dealias)
    for ell, m_ind, ell_ind in b.ell_maps:
        v['c'][0, m_ind, ell_ind, :] = (ell+2)*uk0['c'][0, m_ind, ell_ind, :]
        v['c'][1, m_ind, ell_ind, :] = (ell+4)*uk0['c'][1, m_ind, ell_ind, :]
        v['c'][2, m_ind, ell_ind, :] = (ell+3)*uk0['c'][2, m_ind, ell_ind, :]
    func = lambda ell: ell+3
    w = operators.SphericalEllProduct(u, c, func).evaluate()
    assert np.allclose(w['g'], v['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('layout', ['c', 'g'])
def test_convert_scalar(Nphi, Ntheta, Nr, k, dealias, basis, dtype, layout):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = 3*x**2 + 2*y*z
    g = operators.Laplacian(f, c).evaluate()
    f.require_layout(layout)
    g.require_layout(layout)
    h = (f + g).evaluate()
    assert np.allclose(h['g'], f['g'] + g['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('layout', ['c', 'g'])
def test_convert_vector(Nphi, Ntheta, Nr, k, dealias, basis, dtype, layout):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    u.set_scales(b.domain.dealias)
    u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
    u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
    v = operators.Laplacian(u, c).evaluate()
    u.require_layout(layout)
    v.require_layout(layout)
    w = (u + v).evaluate()
    assert np.allclose(w['g'], u['g'] + v['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('layout', ['c', 'g'])
def test_trace_tensor(Nphi, Ntheta, Nr, k, dealias, basis, dtype, layout):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    u.set_scales(b.domain.dealias)
    u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
    u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
    T = operators.Gradient(u, c).evaluate()
    fg = T['g'][0,0] + T['g'][1,1] + T['g'][2,2]
    T.require_layout(layout)
    f = operators.Trace(T).evaluate()
    assert np.allclose(f['g'], fg)


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('layout', ['c', 'g'])
def test_transpose_tensor(Nphi, Ntheta, Nr, k, dealias, dtype, basis, layout):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    u.set_scales(b.domain.dealias)
    u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
    u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
    T = operators.Gradient(u, c).evaluate()
    Tg = np.transpose(np.copy(T['g']),(1,0,2,3,4))
    T.require_layout(layout)
    T = operators.TransposeComponents(T).evaluate()
    assert np.allclose(T['g'], Tg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Ntheta', [8])
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_interpolate_scalar(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    f['g'] = x**4 + 2*y**4 + 3*z**4
    h = operators.interpolate(f, r=radius).evaluate()
    hg = (radius)**4*(3*np.cos(theta)**4 + np.cos(phi)**4*np.sin(theta)**4 + 2*np.sin(theta)**4*np.sin(phi)**4)
    assert np.allclose(h['g'], hg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Ntheta', [8])
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_interpolate_vector(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    u.set_scales(b.domain.dealias)
    u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
    u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
    v = operators.interpolate(u, r=radius).evaluate()
    vg = 0 * v['g']
    vg[0] = radius**2*sp*(-2*ct**2+radius*ct*cp*st**2*sp-radius**3*cp**2*st**5*sp**3)
    vg[1] = radius**2*(2*ct**3*cp-radius*cp**3*st**4+radius**3*ct*cp**3*st**5*sp**3-1/16*radius*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    vg[2] = radius**2*st*(2*ct**2*cp-radius*ct**3*sp+radius**3*cp**3*st**5*sp**3+radius*ct*st**2*(cp**3+sp**3))
    assert np.allclose(v['g'], vg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Ntheta', [8])
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_interpolate_tensor(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    T = field.Field(dist=d, bases=(b,), tensorsig=(c,c), dtype=dtype)
    T.set_scales(b.domain.dealias)
    T['g'][2,2] = (6*x**2+4*y*z)/r**2
    T['g'][2,1] = T['g'][1,2] = -2*(y**3+x**2*(y-3*z)-y*z**2)/(r**3*np.sin(theta))
    T['g'][2,0] = T['g'][0,2] = 2*x*(z-3*y)/(r**2*np.sin(theta))
    T['g'][1,1] = 6*x**2/(r**2*np.sin(theta)**2) - (6*x**2+4*y*z)/r**2
    T['g'][1,0] = T['g'][0,1] = -2*x*(x**2+y**2+3*y*z)/(r**3*np.sin(theta)**2)
    T['g'][0,0] = 6*y**2/(x**2+y**2)
    A = operators.interpolate(T, r=radius).evaluate()
    Ag = 0 * A['g']
    Ag[2,2] = 2*np.sin(theta)*(3*np.cos(phi)**2*np.sin(theta)+2*np.cos(theta)*np.sin(phi))
    Ag[2,1] = Ag[1,2] = 6*np.cos(theta)*np.cos(phi)**2*np.sin(theta) + 2*np.cos(2*theta)*np.sin(phi)
    Ag[2,0] = Ag[0,2] = 2*np.cos(phi)*(np.cos(theta) - 3*np.sin(theta)*np.sin(phi))
    Ag[1,1] = 2*np.cos(theta)*(3*np.cos(theta)*np.cos(phi)**2 - 2*np.sin(theta)*np.sin(phi))
    Ag[1,0] = Ag[0,1] = -2*np.cos(phi)*(np.sin(theta) + 3*np.cos(theta)*np.sin(phi))
    Ag[0,0] = 6*np.sin(phi)**2
    assert np.allclose(A['g'], Ag)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Ntheta', [8])
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_radial_component_vector(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    u.set_scales(b.domain.dealias)
    u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
    u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
    v = operators.RadialComponent(operators.interpolate(u, r=radius)).evaluate()
    vg = radius**2*st*(2*ct**2*cp-radius*ct**3*sp+radius**3*cp**3*st**5*sp**3+radius*ct*st**2*(cp**3+sp**3))
    assert np.allclose(v['g'], vg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Ntheta', [8])
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_radial_component_tensor(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    T = field.Field(dist=d, bases=(b,), tensorsig=(c,c), dtype=dtype)
    T.set_scales(b.domain.dealias)
    T['g'][2,2] = (6*x**2+4*y*z)/r**2
    T['g'][2,1] = T['g'][1,2] = -2*(y**3+x**2*(y-3*z)-y*z**2)/(r**3*np.sin(theta))
    T['g'][2,0] = T['g'][0,2] = 2*x*(z-3*y)/(r**2*np.sin(theta))
    T['g'][1,1] = 6*x**2/(r**2*np.sin(theta)**2) - (6*x**2+4*y*z)/r**2
    T['g'][1,0] = T['g'][0,1] = -2*x*(x**2+y**2+3*y*z)/(r**3*np.sin(theta)**2)
    T['g'][0,0] = 6*y**2/(x**2+y**2)
    A = operators.RadialComponent(operators.interpolate(T, r=radius)).evaluate()
    Ag = 0 * A['g']
    Ag[2] = 2*np.sin(theta)*(3*np.cos(phi)**2*np.sin(theta)+2*np.cos(theta)*np.sin(phi))
    Ag[1] = 6*np.cos(theta)*np.cos(phi)**2*np.sin(theta) + 2*np.cos(2*theta)*np.sin(phi)
    Ag[0] = 2*np.cos(phi)*(np.cos(theta) - 3*np.sin(theta)*np.sin(phi))
    assert np.allclose(A['g'], Ag)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Ntheta', [8])
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_angular_component_vector(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    ct, st, cp, sp = np.cos(theta), np.sin(theta), np.cos(phi), np.sin(phi)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    u.set_scales(b.domain.dealias)
    u['g'][2] = r**2*st*(2*ct**2*cp-r*ct**3*sp+r**3*cp**3*st**5*sp**3+r*ct*st**2*(cp**3+sp**3))
    u['g'][1] = r**2*(2*ct**3*cp-r*cp**3*st**4+r**3*ct*cp**3*st**5*sp**3-1/16*r*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    u['g'][0] = r**2*sp*(-2*ct**2+r*ct*cp*st**2*sp-r**3*cp**2*st**5*sp**3)
    v = operators.AngularComponent(operators.interpolate(u, r=radius)).evaluate()
    vg = 0 * v['g']
    vg[0] = radius**2*sp*(-2*ct**2+radius*ct*cp*st**2*sp-radius**3*cp**2*st**5*sp**3)
    vg[1] = radius**2*(2*ct**3*cp-radius*cp**3*st**4+radius**3*ct*cp**3*st**5*sp**3-1/16*radius*np.sin(2*theta)**2*(-7*sp+np.sin(3*phi)))
    assert np.allclose(v['g'], vg)


@pytest.mark.parametrize('Nphi', [16])
@pytest.mark.parametrize('Ntheta', [8])
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('k', k_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('dtype', [np.float64, np.complex128])
@pytest.mark.parametrize('radius', [0.5, 1.0, 1.5])
def test_angular_component_tensor(Nphi, Ntheta, Nr, k, dealias, dtype, basis, radius):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, k, dealias, dtype)
    T = field.Field(dist=d, bases=(b,), tensorsig=(c,c), dtype=dtype)
    T.set_scales(b.domain.dealias)
    T['g'][2,2] = (6*x**2+4*y*z)/r**2
    T['g'][2,1] = T['g'][1,2] = -2*(y**3+x**2*(y-3*z)-y*z**2)/(r**3*np.sin(theta))
    T['g'][2,0] = T['g'][0,2] = 2*x*(z-3*y)/(r**2*np.sin(theta))
    T['g'][1,1] = 6*x**2/(r**2*np.sin(theta)**2) - (6*x**2+4*y*z)/r**2
    T['g'][1,0] = T['g'][0,1] = -2*x*(x**2+y**2+3*y*z)/(r**3*np.sin(theta)**2)
    T['g'][0,0] = 6*y**2/(x**2+y**2)
    A = operators.AngularComponent(operators.interpolate(T, r=radius), index=1).evaluate()
    Ag = 0 * A['g']
    Ag[2,1] = 6*np.cos(theta)*np.cos(phi)**2*np.sin(theta) + 2*np.cos(2*theta)*np.sin(phi)
    Ag[2,0] = 2*np.cos(phi)*(np.cos(theta) - 3*np.sin(theta)*np.sin(phi))
    Ag[1,1] = 2*np.cos(theta)*(3*np.cos(theta)*np.cos(phi)**2 - 2*np.sin(theta)*np.sin(phi))
    Ag[1,0] = Ag[0,1] = -2*np.cos(phi)*(np.sin(theta) + 3*np.cos(theta)*np.sin(phi))
    Ag[0,0] = 6*np.sin(phi)**2
    assert np.allclose(A['g'], Ag)

