"""Class that creates LTI aircraft model."""
import control as ct
import numpy as np
import rich.repr

from data.load_aircraft_data import load_aircraft, AircraftData


@rich.repr.auto
class Aircraft:

    def __init__(self, filename: str) -> None:
        """Initialize aircraft model."""
        self.filename = filename
        self.data = load_aircraft(filename)
        self.sym = None
        self.asym = None

        if self.data.symmetric:
            self.sym = Symmetric(self.data)
        if self.data.asymmetric:
            self.asym = Asymmetric(self.data)

    def __rich_repr__(self) -> rich.repr.Result:
        """Representation of the state space model."""
        yield "Aircraft", self.filename
        yield "Symmetric", self.sym is not None
        yield "Asymmetric", self.asym is not None


class StateSpace(ct.StateSpace):
    a: np.ndarray
    b: np.ndarray
    x_names: list[str]
    u_names: list[str]

    def __init__(self, a: np.ndarray, b: np.ndarray, x_names: list[str], u_names: list[str]) -> None:
        """Initialize state space model."""
        self.a = a
        self.b = b
        self.x_names = x_names
        self.u_names = u_names

        c = np.eye(a.shape[0])
        d = np.zeros((a.shape[0], b.shape[1]))
        super().__init__(a, b, c, d)
        self.set_inputs(u_names)
        self.set_outputs(x_names)
        self.set_states(x_names)


class Symmetric(StateSpace):
    """Symmetric aircraft state space model."""

    def __init__(self, data: AircraftData) -> None:
        """Initialize symmetric aircraft model.

        args:
            data: AircraftData object
        """
        x_names = ['u_hat', 'alpha', 'theta', 'q_cv']
        u_names = ['de']
        a = self.build_a(data)
        b = self.build_b(data)

        super(Symmetric, self).__init__(a, b, x_names, u_names)

    @staticmethod
    def build_a(data: AircraftData) -> np.ndarray:
        """Build A matrix"""
        # Load variables
        v = data.v

        c_bar = data.symmetric.c_bar
        mu_c = data.symmetric.mu_c
        ky_2 = data.symmetric.ky_2

        cx = data.symmetric.cx
        cz = data.symmetric.cz
        cm = data.symmetric.cm

        # Declare repetitive calculations
        v_c = v / c_bar  # v/c_bar
        mu_c_cz_a = 2 * mu_c - cz.a_dot
        cm_a_mu_c = cm.a_dot / (2 * mu_c - cz.a_dot)
        mu_c_ky_2 = 2 * mu_c * ky_2

        xu = v_c * cx.u / (2 * mu_c)
        xa = v_c * cx.a / (2 * mu_c)
        xt = v_c * cz.o / (2 * mu_c)

        zu = v_c * cz.u / mu_c_cz_a
        za = v_c * cz.a / mu_c_cz_a
        zt = v_c * cx.o / mu_c_cz_a
        zq = v_c * (2 * mu_c + cz.q) / mu_c_cz_a

        mu = v_c * (cm.u + cz.u * cm_a_mu_c) / mu_c_ky_2
        ma = v_c * (cm.a + cz.a * cm_a_mu_c) / mu_c_cz_a
        mt = - v_c * (cx.o * cm_a_mu_c) / mu_c_ky_2
        mq = v_c * (cm.q + cm.a_dot * (2 * mu_c + cz.q) / mu_c_cz_a) / mu_c_cz_a

        a = np.array([
            [xu, xa, xt, 0],
            [zu, za, zt, zq],
            [0, 0, 0, v_c],
            [mu, ma, mt, mq]
        ])

        return a

    @staticmethod
    def build_b(data: AircraftData) -> np.ndarray:
        """Build B matrix"""
        # Load variables
        v = data.v

        c_bar = data.symmetric.c_bar
        mu_c = data.symmetric.mu_c
        ky_2 = data.symmetric.ky_2

        cx = data.symmetric.cx
        cz = data.symmetric.cz
        cm = data.symmetric.cm

        # Declare repetitive calculations
        v_c = v / c_bar  # v/c_bar
        mu_c_cz_a = 2 * mu_c - cz.a_dot

        x_de = v_c * cx.de / (2 * mu_c)
        z_de = v_c * cz.de / mu_c_cz_a
        m_de = v_c * (cm.de + cz.de * cm.a_dot / mu_c_cz_a) / (2 * mu_c * ky_2)

        b = np.array([
            [x_de],
            [z_de],
            [0],
            [m_de]
        ])

        return b


class Asymmetric(StateSpace):
    """Asymmetric aircraft state space model."""

    def __init__(self, data: AircraftData) -> None:
        """Initialize asymmetric aircraft model.

        args:
            data: AircraftData object
        """
        x_names = ['beta', 'phi', 'pb_2v', 'rb_2v']
        u_names = ['da', 'dr']
        a = self.build_a(data)
        b = self.build_b(data)

        super(Asymmetric, self).__init__(a, b, x_names, u_names)

    @staticmethod
    def build_a(data: AircraftData) -> np.ndarray:
        """Build A matrix"""
        # Load variables
        v = data.v

        b = data.asymmetric.b
        mu_b = data.asymmetric.mu_b
        c_l = data.asymmetric.c_l
        kx_2 = data.asymmetric.kx_2
        kz_2 = data.asymmetric.kz_2
        kxz = data.asymmetric.kxz

        cy = data.asymmetric.cy
        cl = data.asymmetric.cl
        cn = data.asymmetric.cn

        # Declare repetitive calculations
        v_b = v / b
        mu_b_k = 4 * mu_b * (kx_2 * kz_2 - kxz ** 2)

        yb = v_b * cy.b / (2 * mu_b)
        yphi = v_b * c_l / (2 * mu_b)
        yp = v_b * cy.p / (2 * mu_b)
        yr = v_b * (cy.r - 4 * mu_b) / (2 * mu_b)

        lb = v_b * (cl.b * kz_2 + cn.b * kxz) / mu_b_k
        lp = v_b = (cl.p * kz_2 + cn.p * kxz) / mu_b_k
        lr = v_b = (cl.r * kz_2 + cn.r * kxz) / mu_b_k

        nb = v_b * (cl.b * kxz + cn.b * kx_2) / mu_b_k
        n_p = v_b * (cl.p * kxz + cn.p * kx_2) / mu_b_k
        nr = v_b * (cl.r * kxz + cn.r * kx_2) / mu_b_k

        a = np.array([
            [yb, yphi, yp, yr],
            [0, 0, 2 * v_b, 0],
            [lb, 0, lp, lr],
            [nb, 0, n_p, nr]
        ])

        return a

    @staticmethod
    def build_b(data: AircraftData) -> np.ndarray:
        """Build B matrix."""
        # Load variables
        v = data.v

        mu_b = data.asymmetric.mu_b
        kx_2 = data.asymmetric.kx_2
        kz_2 = data.asymmetric.kz_2
        kxz = data.asymmetric.kxz

        cy = data.asymmetric.cy
        cl = data.asymmetric.cl
        cn = data.asymmetric.cn

        # Declare repetitive calculations
        v_b = v / mu_b
        mu_b_k = 4 * mu_b * (kx_2 * kz_2 - kxz ** 2)

        y_dr = v_b * cy.dr / (2 * mu_b)

        l_da = v_b * (cl.da * kz_2 + cn.da * kxz) / mu_b_k
        l_dr = v_b * (cl.dr * kz_2 + cn.dr * kxz) / mu_b_k

        n_da = v_b * (cl.da * kxz + cn.da * kx_2) / mu_b_k
        n_dr = v_b * (cl.dr * kxz + cn.dr * kx_2) / mu_b_k

        b = np.array([
            [0, y_dr],
            [0, 0],
            [l_da, l_dr],
            [n_da, n_dr]
        ])

        return b
