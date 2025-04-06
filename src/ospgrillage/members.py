# -*- coding: utf-8 -*-
"""
This module manages user interface functions and class definitions for
grillage members. In our terminology, we define a section as the geometrical
properties of the structural elements, and the member as the combination of
the section and material properties.
"""
from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from material import Material


def create_section(**kwargs):
    """
    User interface function to create :class:`Section` object.

    The constructor :class:`Section` takes the following arguments.

    :param op_ele_type: OpenSees element type - default is "elasticBeamColumn"
    :type op_ele_type: str
    :param op_section_type: OpenSees section type - default is "Elastic"
    :type op_section_type: str
    :param unit_width: Flag for unit width properties
    :type unit_width: bool

    The constructor of :class:`Section` takes the following ``kwargs``:

    :keyword:

    * A (`float`): Cross sectional area
    * Iz (`float`): Moment of inertia about local z axis
    * Iy (`float`): Moment of inertia about local y axis
    * J (`float`): Torsional inertia - about local x axis
    * Az (`float`): Cross sectional area in the local z direction
    * Ay (`float`): Cross sectional area in the local y direction


    :return: :class:`Section` object
    """
    return Section(**kwargs)


def create_member(**kwargs):
    """
    User interface function to create :class:`GrillageMember` object.

    A grillage member requires a :class:`~ospgrillage.material.Material` and a
    :class:`~ospgrillage.members.Section`.

    :param section: Section class object
    :type section: :class:`Section`
    :param material: Material class object
    :type material: :class:`~ospgrillage.material.Material`
    :param member_name: Name of the grillage member (Optional)
    :type member_name: str

    :returns: :class:`~ospgrillage.members.GrillageMember` object
    """
    return GrillageMember(**kwargs)


class Section:
    """
    Class for structural sections of grillage model. Stores geometric properties of cross sections. This class also
    parses section inputs into relevant
    ``OpenSeesPy`` command for creating sections in OpenSees framework.

    This class wraps ```OpenSeesPy``` Section() commands - methods for generating commands are handled by the
    higher hierarchy:class:`~ospgrillage.member.GrillageMember` class

    """

    def __init__(
        self,
        op_ele_type: str = "elasticBeamColumn",
        mass: float = 0,
        c_mass_flag: bool = False,
        unit_width: bool = False,
        op_section_type: str = "Elastic",
        **kwargs,
    ):
        """
        The constructor takes in two types of keyword arguments.

        #. General section properties - such as A, I, J for example. These properties are parses into the appropriate
           OpenSees section arguments.
        #. ``OpenSeespy`` section arguments - i.e. specific keyword for a specific ops.section() type.

        `Section <https://openseespydoc.readthedocs.io/en/latest/src/section.html>`_  information of OpenSeesPy

        Constructor takes following inputs to be parse into arguments for ```OpenSeesPy``` Sections.

        :param op_ele_type: OpenSees element type - default elasticBeamColumn
        :type op_ele_type: str
        :param op_section_type: OpenSees section type - default Elastic
        :type op_section_type: str
        :param mass: Mass of member.
        :type mass: float
        :param unit_width: Flag for if unit width properties are defined.
        :type unit_width: bool

        Constructor also takes the following keyword arguments for a section.

        :keyword:
        * A (``float``): Cross sectional area
        * Iz (``float``): Moment of inertia about local z axis
        * Iy (``float``): Moment of inertia about local y axis
        * J (``float``): Torsional inertia - about local x axis
        * Az (``float``): Cross sectional area in the local z direction
        * Ay (``float``): Cross sectional area in the local y direction

        .. note::
        Section properties are defined in local coordinate x y and z which are later transformed according to orientation
        of the defined GrillageMember object in the grillage model.
        """
        # OpenSees py section type
        self.op_section_type = (
            op_section_type  # section tag based on OpenSeesPy - default is elastic
        )
        self.section_command_flag = False  # flag for parsing , check if section() command is needed. default False
        # OpenSeesPy section arguments
        # standard geometric properties
        self.A = kwargs.get("A", None)
        self.Iz = kwargs.get("Iz", None)
        self.Iy = kwargs.get("Iy", None)
        # for 3D sections
        self.Ay = kwargs.get("Ay", None)
        self.Az = kwargs.get("Az", None)
        self.J = kwargs.get("J", None)
        # for non-linear properties
        self.alpha_y = kwargs.get("alpha_y", None)
        self.alpha_z = kwargs.get("alpha_z", None)
        self.K11 = kwargs.get("K11", None)
        self.K33 = kwargs.get("K33", None)
        self.K44 = kwargs.get("K44", None)
        # for quad elements
        self.h_depth = kwargs.get("h", None)

        # types for element definition and unit width properties
        self.op_ele_type = op_ele_type
        self.unit_width = unit_width
        self.mass = mass
        self.c_mass_flag = c_mass_flag
        # keyword args
        self.num_int_pt = kwargs.get("num_int_pt", None)
        self.integration_type = kwargs.get("integration_type", None)
        # quad/tri element parameters
        self.thick = kwargs.get("thick", None)
        # for quad elements
        # here check and overwrite element if  h_depth is given, default to quad shell element
        if self.h_depth:
            self.op_section_type = "ElasticMembranePlateSection"
            self.op_ele_type = "ShellDKGQ"
        # warning checks
        E = kwargs.get("E", None)
        G = kwargs.get("G", None)
        if any([E, G]):
            raise ValueError(
                "E or G is provided to Section object. Hint: E and G are attributes of Material Object"
            )
        self.parse_section_properties()

    def parse_section_properties(self):
        # function to parse input properties
        # mainly, this is used to define less essential properties (e.g. Ay, Az) which user may not specify
        # but is required for the model commands
        # for developers, add here the section properties which needs to be parse for model command
        if self.Ay is None and self.A is not None:
            self.Ay = 0.5 * self.A
        if self.Az is None and self.A is not None:
            self.Az = 0.2 * self.A
        if self.Iy is None and self.Iz is not None:
            self.Iy = 0.2 * self.Iz


# ----------------------------------------------------------------------------------------------------------------


class GrillageMember:
    """
    Class for grillage model members. E.g., longitudinal beam members.

    This class parses material and section properties of grillage members into corresponding ``OpenSeesPy`` Element()
    command.

    `Refer here <https://openseespydoc.readthedocs.io/en/latest/src/element.html>`_ for more information about
     ``OpenSeesPy`` Element types and definition workflow.

    For developers wishing to expand the library of elements wrapped by GrillageMember, introduce in this class:

    #. The argument input orders of new element in :func:`~ospgrillage.member.GrillageMember.get_member_prop_arguments`
     method.
    #. If the element requires the definition of Section in ``OpenSeesPy``, add its Section's list of input arguments
     command generation to :func:`~ospgrillage.member.GrillageMember.get_section_arguments` and
     :func:`~ospgrillage.member.GrillageMember.get_ops_section_command`.

    """

    def __init__(
        self,
        section: Section,
        material,
        member_name: str = "Undefined",
        quad_ele_flag: bool = False,
        tri_ele_flag: bool = False,
        release_y: bool = False,
        release_z: bool = False,
        validate_releases: bool = True,
        is_transverse_slab: bool = False,
    ):
        """
        Init the GrillageMember. Requires two input objects i.e. A :class:`~ospgrillage.material.Material`, and
        :class:`Section`.

        :param section: Section class object
        :type section: :class:`~ospgrillage.members.Section`
        :param material: Material class object
        :type material: :class:`~ospgrillage.material.Material`
        :param member_name: Name of the grillage member (Optional)
        :type member_name: str
        :param release_y: Flag to add y-direction release (Optional)
        :type release_y: bool
        :param release_z: Flag to add z-direction release (Optional)
        :type release_z: bool
        :param validate_releases: Flag to validate releases to prevent instability (Optional)
        :type validate_releases: bool
        :param is_transverse_slab: Flag to indicate if this is a transverse slab member (Optional)
        :type is_transverse_slab: bool
        """
        self.member_name = member_name
        self.section = section
        self.material = material
        self.quad_flag = quad_ele_flag
        self.tri_ele_flag = tri_ele_flag
        self.release_y = release_y
        self.release_z = release_z
        self.validate_releases = validate_releases
        self.is_transverse_slab = is_transverse_slab
        self.section_command_flag = True
        self.material_command_flag = True
        if any(
            [
                self.section.op_ele_type == "ElasticTimoshenkoBeam",
                self.section.op_ele_type == "elasticBeamColumn",
            ]
        ):
            self.material_command_flag = False
            self.section_command_flag = False  #

            # determine mass from section area and material density
            self.mass = self.section.A * self.material.density
        elif any(
            [
                self.section.op_ele_type == "ShellMITC4",
                self.section.op_ele_type == "ShellDKGQ",
            ]
        ):
            self.material_command_flag = False

        self.variable_string_list = []

    def get_member_prop_arguments(self, width=1):
        """
        Returns the element arguments based on the op_element_type of the GrillageMember.

        :return: str containing member properties in accordance with convention of OpenSees element type
        """

        asterisk_input = None

        # if elastic Beam column elements, return str of section input
        if self.section.op_ele_type == "ElasticTimoshenkoBeam":
            if None in [
                self.material.elastic_modulus,
                self.material.shear_modulus,
                self.section.A,
                self.section.J,
                self.section.Iy,
                self.section.Iz,
                self.section.Ay,
                self.section.Az,
            ]:
                raise ValueError(
                    "One or more missing arguments for Section: {}".format(
                        self.section.op_ele_type
                    )
                )
            asterisk_input = "[{:.3e}, {:.3e}, {:.3e}, {:.3e}, {:.3e}, {:.3e}, {:.3e}, {:.3e}]".format(
                self.material.elastic_modulus,
                self.material.shear_modulus,
                self.section.A * width,
                self.section.J * width,
                self.section.Iy * width,
                self.section.Iz * width,
                self.section.Ay * width,
                self.section.Az * width,
            )
        elif self.section.op_ele_type == "elasticBeamColumn":  # eleColumn
            if None in [
                self.material.elastic_modulus,
                self.material.shear_modulus,
                self.section.A,
                self.section.J,
                self.section.Iy,
                self.section.Iz,
            ]:
                raise ValueError(
                    "One or more missing arguments for Section: {}".format(
                        self.section.op_ele_type
                    )
                )

            asterisk_input = "[{:.3e}, {:.3e}, {:.3e}, {:.3e}, {:.3e}, {:.3e}]".format(
                self.section.A * width,
                self.material.elastic_modulus,
                self.material.shear_modulus,
                self.section.J * width,
                self.section.Iy * width,
                self.section.Iz * width,
            )

        return asterisk_input

    # Function to return argument, handled by OspGrillage
    def get_section_arguments(self, ele_width: float = 1):
        """
        Returns the input arguments for ``OpenSeesPy`` Section command if the prescribe element type of the
        GrillageMember requires the definition of an ``OpenSeesPy`` Section object.

        :return: str containing Section command properties in accordance with convention of OpenSees element type
        """
        section_args = None

        if self.section.op_section_type == "Elastic":
            section_args = [
                self.material.elastic_modulus,
                self.section.A,
                self.section.Iz,
                self.section.Iy,
                self.material.shear_modulus,
                self.section.J,
                self.section.alpha_y,
                self.section.alpha_z,
            ]

        return section_args

    def get_ops_section_command(
        self, section_tag: int = 1, material_tag: int = None, ele_width: float = 1
    ):
        """
        Returns the ``OpenSeesPy`` Section command for the Section type

        :return: str containing the ``OpenSeesPy`` Section command
        """
        sec_str = None
        section_type = self.section.op_section_type
        if section_type == "Elastic":
            # section type, section tag, argument entries from self.get_asterisk_input()
            sec_arg = self.get_section_arguments(ele_width=ele_width)
            sec_str = 'ops.section("{type}", {tag}, *{arg})\n'.format(
                type=section_type, tag=section_tag, arg=repr(sec_arg)
            )
        elif section_type == "ElasticMembranePlateSection":
            # section type, section tag, E_mod, nu, h, rho
            sec_str = (
                'ops.section("{type}", {tag}, {E_mod}, {nu}, {h}, {rho})\n'.format(
                    type=section_type,
                    tag=section_tag,
                    E_mod=self.material.elastic_modulus,
                    nu=self.material.poisson_ratio,
                    h=self.section.h_depth,
                    rho=self.material.density,
                )
            )
        elif section_type == "PlateFiber":
            # section type, section tag, E_mod, nu, h, rho
            sec_str = 'ops.section("{type}", {tag}, {mat_tag}, {h})\n'.format(
                type=section_type,
                tag=section_tag,
                h=self.section.h_depth,
                mat_tag=material_tag,
            )

        return sec_str

    def get_element_command_str(
        self,
        ele_tag: int,
        node_tag_list: list,
        transf_tag: int = None,
        ele_width: float = 1,
        materialtag: int = None,
        sectiontag: int = None,
    ) -> str:
        """Return a list of OpenSeesPy element command for the member.
        This function is handled by OspGrillage class.
        """
        section_input = None
        ele_str = None
        
        # Validate releases if enabled
        if self.validate_releases and (self.release_y or self.release_z):
            # Don't allow both y and z releases on same element as it creates a mechanism
            if self.release_y and self.release_z:
                raise ValueError("Cannot release both y and z directions on the same element as it would create a mechanism")
            
            # Don't allow releases on elements that would create instability
            if len(node_tag_list) != 2:
                raise ValueError("Releases can only be applied to 2-node elements")
            
            # Special validation for transverse slabs
            if self.is_transverse_slab:
                # For transverse slabs, only allow z-direction release
                if self.release_y:
                    raise ValueError("Cannot add y-direction release to transverse slab elements")
                # Only allow z-direction release if it's not at the support
                if self.release_z:
                    # Check if either node is at a support
                    if any(node in self.Mesh_obj.edge_node_recorder for node in node_tag_list):
                        raise ValueError("Cannot add z-direction release to transverse slab elements at supports")

        if self.section.op_ele_type == "ElasticTimoshenkoBeam":
            section_input = self.get_member_prop_arguments(ele_width)
            # Add releases if specified
            release_str = ""
            if self.release_z:
                release_str += ", '-releasez', 3"
            if self.release_y:
                release_str += ", '-releasey', 3"
                
            ele_str = 'ops.element("{type}", {tag}, *{node_tag_list}, *{memberprop}, {transftag}{releases}, {mass})\n'.format(
                type=self.section.op_ele_type,
                tag=ele_tag,
                node_tag_list=node_tag_list,
                memberprop=section_input,
                transftag=transf_tag,
                releases=release_str,
                mass=self.mass,
            )
        elif self.section.op_ele_type == "elasticBeamColumn":
            section_input = self.get_member_prop_arguments(ele_width)
            # Add releases if specified
            release_str = ""
            if self.release_z:
                release_str += ", '-releasez', 3"
            if self.release_y:
                release_str += ", '-releasey', 3"
                
            ele_str = 'ops.element("{type}", {tag}, *{node_tag_list}, *{memberprop}, {transftag}{releases}, {mass})\n'.format(
                type=self.section.op_ele_type,
                tag=ele_tag,
                node_tag_list=node_tag_list,
                memberprop=section_input,
                transftag=transf_tag,
                releases=release_str,
                mass=self.mass,
            )
        elif self.section.op_ele_type == "nonlinearBeamColumn":
            ele_str = 'ops.element("{type}",{tag},*{node_tag_list},{num_int_pt},{sectag},{transftag},{mass})\n'.format(
                type=self.section.op_ele_type,
                tag=ele_tag,
                node_tag_list=node_tag_list,
                num_int_pt=self.section.num_int_pt,
                sectag=sectiontag,
                transftag=transf_tag,
                mass=self.mass,
            )
        elif self.section.op_ele_type == "zeroLength":
            ele_str = "ops.element(\"{linktype}\",{ele_tag},*[{rNodetag},{cNodetag}],'-mat',{mat_tag},'-dir',{dirs})\n".format(
                linktype=self.section.op_ele_type,
                rNodetag=node_tag_list[0],
                cNodetag=node_tag_list[1],
                dirs=6,
                mat_tag=materialtag,
                ele_tag=ele_tag,
            )

        # for shell element option
        elif self.section.op_ele_type == "ShellMITC4":
            ele_str = (
                'ops.element("{type}", {tag}, *{node_tag_list}, {sectag})\n'.format(
                    type=self.section.op_ele_type,
                    tag=ele_tag,
                    node_tag_list=node_tag_list,
                    sectag=sectiontag,
                )
            )

        elif self.section.op_ele_type == "ShellDKGQ":
            if len(node_tag_list) == 3:
                ele_type = "ShellDKGT"
            else:  # 4 node
                ele_type = "ShellDKGQ"
            ele_str = (
                'ops.element("{type}", {tag}, *{node_tag_list}, {sectag})\n'.format(
                    type=ele_type,
                    tag=ele_tag,
                    node_tag_list=node_tag_list,
                    sectag=sectiontag,
                )
            )

        elif self.section.op_ele_type == "ShellDKGT":
            ele_str = (
                'ops.element("{type}", {tag}, *{node_tag_list}, {sectag})\n'.format(
                    type=self.section.op_ele_type,
                    tag=ele_tag,
                    node_tag_list=node_tag_list,
                    sectag=sectiontag,
                )
            )

        return ele_str
